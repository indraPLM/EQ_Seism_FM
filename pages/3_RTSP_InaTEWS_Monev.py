# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from obspy.geodetics import degrees2kilometers

# 🌍 Page configuration
st.set_page_config(page_title='TSP Monitoring dan Evaluasi', layout='wide', page_icon="🌍")

# 🎛 Sidebar input
st.sidebar.header("Parameter Waktu")
time_start = pd.to_datetime(st.sidebar.text_input('Start DateTime:', '2024-11-01'))
time_end = pd.to_datetime(st.sidebar.text_input('End DateTime:', '2025-01-31'))

# 🛠️ Utility Functions
def fix_coord(val):
    return -float(val[:-1]) if val[-1] in 'SW' else float(val[:-1])

def fetch_rtsp_page(url):
    soup = BeautifulSoup(requests.get(url).text, 'html')
    rows = soup.find_all("td", {"class": "txt11pxarialb"})
    data = [div.text for row in rows for div in row.find_all('div')]
    chunks = [data[i:i + 9] for i in range(0, len(data), 9)]
    records = []
    for row in chunks:
        try:
            records.append({
                'date_time': f"{row[0]} {row[1]}",
                'mag': float(row[2]),
                'depth': float(row[3]),
                'lat': fix_coord(row[4]),
                'lon': fix_coord(row[5]),
                'typ': row[6], 'num_bull': row[7], 'evt_group': row[8]
            })
        except: continue
    return pd.DataFrame(records)

def normalize_bmkg_time(df):
    df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')
    df['date_time'] = df['date_time'].dt.tz_localize('Asia/Jakarta', ambiguous='NaT').dt.tz_convert('UTC')
    df['sizemag'] = df['mag'] * 1000
    return df

def fetch_dissemination_times(event_groups):
    results = []
    for group in event_groups:
        try:
            soup = BeautifulSoup(requests.get(f"https://rtsp.bmkg.go.id/timelinepub.php?grup={group}").text, 'html')
            rows = [div.text for td in soup.find_all("td", {"class": "txt12pxarialb"}) for div in td.find_all('div')]
            ot_dt = pd.to_datetime(" ".join(rows[0].split()[1:3]))
            diss_dt = pd.to_datetime(" ".join(rows[1].split()[0:2]))
            results.append({
                'OT_datetime': ot_dt,
                'Diss_datetime': diss_dt,
                'Lapse_Time': diss_dt - ot_dt
            })
        except: continue
    return pd.DataFrame(results)

# 🗂 Load BMKG RTSP Pages (halaman 1-14)
bmkg_pages = [fetch_rtsp_page(f'https://rtsp.bmkg.go.id/publicbull.php?halaman={i}') for i in range(1, 15)]
df_rtsp = pd.concat(bmkg_pages, ignore_index=True)
df_rtsp = normalize_bmkg_time(df_rtsp)

# 🌐 Load USGS Catalog
usgs_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2014-01-01&endtime={time_end.date()}&minmagnitude=6.0"
df_usgs = pd.read_csv(usgs_url)
df_usgs['fix_dateusgs'] = pd.to_datetime(df_usgs['time'], utc=True)

# 🗺 Peta RTSP
st.markdown("### 📍 Peta Gempabumi RTSP BMKG")
st.map(df_rtsp, latitude="lat", longitude="lon", size="sizemag")
st.markdown("### Tabel RTSP BMKG")
st.dataframe(df_rtsp)

# 🗺 Peta USGS
st.markdown("### 🌎 Peta Gempabumi USGS M > 6")
st.map(df_usgs, latitude="latitude", longitude="longitude")
st.markdown("### Tabel USGS Significant EQ")
st.dataframe(df_usgs)

# 🔁 Matching Events
def find_nearby_events(df_rtsp, df_usgs, max_seconds=30):
    matches = []
    for bmkg in df_rtsp.itertuples(index=False):
        bmkg_time = pd.to_datetime(bmkg.date_time, utc=True, errors='coerce')
        if not pd.notnull(bmkg_time): continue
        for usgs in df_usgs.itertuples(index=False):
            usgs_time = pd.to_datetime(usgs.fix_dateusgs, utc=True, errors='coerce')
            if not pd.notnull(usgs_time): continue
            lapse = abs((bmkg_time - usgs_time).total_seconds())
            if lapse <= max_seconds:
                matches.append({
                    'date_bmkg': bmkg_time,
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
df_tsp = df_tsp[(df_tsp['date_time'] >= time_start) & (df_tsp['date_time'] <= time_end)]

# 📊 Difference Metrics
df_tsp['mag_diff'] = abs(df_tsp['mag_bmkg'] - df_tsp['mag_usgs'])
df_tsp['depth_diff'] = abs(df_tsp['depth_bmkg'] - df_tsp['depth_usgs'])
df_tsp['distance_diff_km'] = np.sqrt(
    degrees2kilometers(abs(df_tsp['lon_bmkg'] - df_tsp['lon_usgs'])) ** 2 +
    degrees2kilometers(abs(df_tsp['lat_bmkg'] - df_tsp['lat_usgs'])) ** 2
)

# 📈 Visuals
st.markdown("### 📉 Selisih Magnitudo USGS - BMKG")
st.line_chart(df_tsp, x="date_bmkg", y="mag_diff")

st.markdown("### 📉 Selisih Kedalaman USGS - BMKG")
st.line_chart(df_tsp, x="date_bmkg", y="depth_diff")

st.markdown("### 📉 Selisih Jarak USGS - BMKG")
st.line_chart(df_tsp, x="date_bmkg", y="distance_diff_km")

st.markdown("### 📋 Tabel Perbandingan Parameter Gempa USGS - BMKG")
st.dataframe(df_tsp)

# ⏱ Diseminasi Time
df_diss = fetch_dissemination_times(df_tsp['event_group'].dropna().unique())
st.markdown("### ⏱ Tabel Waktu Kirim OT vs Diseminasi RTSP BMKG")
st.dataframe(df_diss)
