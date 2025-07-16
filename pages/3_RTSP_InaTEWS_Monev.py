import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from obspy.geodetics import degrees2kilometers

st.set_page_config(page_title='TSP Monitoring dan Evaluasi', layout='wide', page_icon="🌍")

# Sidebar inputs
st.sidebar.header("Input Parameter :")
time_start = pd.to_datetime(st.sidebar.text_input('Start DateTime:', '2024-11-01'))
time_end = pd.to_datetime(st.sidebar.text_input('End DateTime:', '2025-01-31'))

# --- Utility Functions ---
def fix_coord(val):
    return -float(val[:-1]) if val[-1] in 'SW' else float(val[:-1])

def split_chunks(lst, size): return [lst[i:i + size] for i in range(0, len(lst), size)]

def fetch_rtsp_page(url):
    soup = BeautifulSoup(requests.get(url).text, 'html')
    rows = soup.find_all("td", {"class": "txt11pxarialb"})
    data = [div.text for row in rows for div in row.find_all('div')]
    chunks = split_chunks(data, 9)
    return pd.DataFrame([{
        'date_time': f"{row[0]} {row[1]}",
        'mag': float(row[2]), 'depth': float(row[3]),
        'lat': fix_coord(row[4]), 'lon': fix_coord(row[5]),
        'typ': row[6], 'num_bull': row[7], 'evt_group': row[8]
    } for row in chunks])

# --- Load RTSP BMKG Data ---
df_rtsp = pd.concat([fetch_rtsp_page(f'https://rtsp.bmkg.go.id/publicbull.php?halaman={i}') for i in range(1, 15)], ignore_index=True)
df_rtsp['date_time'] = pd.to_datetime(df_rtsp['date_time'])
df_rtsp['sizemag'] = df_rtsp['mag'] * 1000

# --- Load USGS Data ---
usgs_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2014-01-01&endtime={time_end.date()}&minmagnitude=6.0"
df_usgs = pd.read_csv(usgs_url)
df_usgs['fix_dateusgs'] = pd.to_datetime(df_usgs['time'])

# --- RTSP Maps & Table ---
st.markdown("### Peta Lokasi Gempabumi berdasarkan Diseminasi RTSP")
st.map(df_rtsp, latitude="lat", longitude="lon", size="sizemag")
st.markdown("### Tabel RTSP BMKG")
st.dataframe(df_rtsp)

# --- USGS Maps & Table ---
st.markdown("### Peta Lokasi Gempabumi M > 6 Katalog USGS")
st.map(df_usgs, latitude="latitude", longitude="longitude")
st.markdown("### Tabel USGS EQ Significant")
st.dataframe(df_usgs)

# --- Match Events Based on Timing ---
def find_nearby_events(df_bmkg, df_usgs, max_seconds=20):
    matches = []
    for bmkg in df_bmkg.itertuples(index=False):
        dt_bmkg = pd.to_datetime(bmkg.date_time, errors='coerce')
        if not pd.notnull(dt_bmkg):
            continue  # skip invalid BMKG time
        for usgs in df_usgs.itertuples(index=False):
            dt_usgs = pd.to_datetime(usgs.fix_dateusgs, errors='coerce')
            if not pd.notnull(dt_usgs):
                continue  # skip invalid USGS time
            lapse = abs((dt_bmkg - dt_usgs).total_seconds())
            if lapse <= max_seconds:
                matches.append({
                    'date_bmkg': dt_bmkg,
                    'date_usgs': usgs.time,
                    'lapse_time(s)': lapse,
                    'loc_bmkg': usgs.place,
                    'lon_bmkg': bmkg.lon,
                    'lon_usgs': usgs.longitude,
                    'lat_bmkg': bmkg.lat,
                    'lat_usgs': usgs.latitude,
                    'mag_bmkg': bmkg.mag,
                    'mag_usgs': usgs.mag,
                    'depth_bmkg': bmkg.depth,
                    'depth_usgs': usgs.depth,
                    'event_group': bmkg.evt_group
                })
    return pd.DataFrame(matches)


df_tsp = find_nearby_events(df_rtsp, df_usgs)
df_tsp['mag_diff'] = abs(df_tsp['mag_bmkg'] - df_tsp['mag_usgs'])
df_tsp['depth_diff'] = abs(df_tsp['depth_bmkg'] - df_tsp['depth_usgs'])
df_tsp['distance_diff_km'] = np.sqrt(
    degrees2kilometers(abs(df_tsp['lon_bmkg'] - df_tsp['lon_usgs'])) ** 2 +
    degrees2kilometers(abs(df_tsp['lat_bmkg'] - df_tsp['lat_usgs'])) ** 2
)
df_tsp = df_tsp[(df_tsp['date_bmkg'] >= time_start) & (df_tsp['date_bmkg'] <= time_end)]

# --- Charts ---
st.markdown("### Grafik Selisih Magnitudo USGS - BMKG (RTSP)")
st.line_chart(df_tsp, x="date_bmkg", y="mag_diff")

st.markdown("### Grafik Selisih Kedalaman USGS - BMKG (RTSP)")
st.line_chart(df_tsp, x="date_bmkg", y="depth_diff")

st.markdown("### Grafik Selisih Jarak USGS - BMKG (RTSP)")
st.line_chart(df_tsp, x="date_bmkg", y="distance_diff_km")

st.markdown("### Tabel Perbandingan Parameter Gempa USGS - BMKG(RTSP)")
st.dataframe(df_tsp)

# --- Fetch Dissemination Time ---
def fetch_dissemination_times(event_groups):
    all_times = []
    for group in event_groups:
        soup = BeautifulSoup(requests.get(
            f"https://rtsp.bmkg.go.id/timelinepub.php?id=&session_id=&grup={group}").text, 'html')
        rows = soup.find_all("td", {"class": "txt12pxarialb"})
        texts = [div.text for row in rows for div in row.find_all('div')]
        if len(texts) >= 2:
            ot_parts = texts[0].split()
            diss_parts = texts[1].split()
            ot_dt = pd.to_datetime(f"{ot_parts[1]} {ot_parts[2]}")
            diss_dt = pd.to_datetime(f"{diss_parts[0]} {diss_parts[1]}")
            all_times.append({'OT_datetime': ot_dt, 'Diss_datetime': diss_dt, 'Lapse_Time': diss_dt - ot_dt})
    return pd.DataFrame(all_times)

df_diss = fetch_dissemination_times(df_tsp['event_group'].dropna().unique())
st.markdown("### Tabel Perbandingan Waktu Kirim OT dan Diseminasi BMKG(RTSP)")
st.dataframe(df_diss)
