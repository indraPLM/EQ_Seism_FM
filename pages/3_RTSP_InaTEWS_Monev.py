# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import requests, datetime
from bs4 import BeautifulSoup
from obspy.geodetics import degrees2kilometers

# 🌍 Page configuration
st.set_page_config(page_title='TSP Monitoring dan Evaluasi', layout='wide', page_icon="🌍")

# 🎛 Sidebar input
st.sidebar.header("Parameter Waktu")
tim_end_def = datetime.datetime.now()
tim_sta_def = tim_end_def - datetime.timedelta(days=30)
tim_sta = pd.to_datetime(
    st.sidebar.date_input("Start Date", tim_sta_def)
).tz_localize('UTC')
tim_end = pd.to_datetime(
    st.sidebar.date_input("End Date", tim_end_def)
).tz_localize('UTC')


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
usgs_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2014-01-01&endtime={tim_end.date()}&minmagnitude=6.0"
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

# After you've finished loading and normalizing BMKG and USGS:
from datetime import timedelta

df_rtsp['date_time'] = pd.to_datetime(df_rtsp['date_time'], errors='coerce') + timedelta(hours=7)
df_rtsp_filtered = df_rtsp[(df_rtsp['date_time'] >= tim_sta) & (df_rtsp['date_time'] <= tim_end)]

df_usgs['fix_dateusgs'] = pd.to_datetime(df_usgs['time'], utc=True)
df_usgs_filtered = df_usgs[(df_usgs['fix_dateusgs'] >= tim_sta) & (df_usgs['fix_dateusgs'] <= tim_end)]

# 🔁 Comparison function (add above if not already defined)
def compare_events(df1, df2, time_col1, time_col2, threshold_seconds=30):
    results = []
    for row1 in df1.itertuples(index=False):
        t1 = getattr(row1, time_col1)
        for row2 in df2.itertuples(index=False):
            t2 = getattr(row2, time_col2)
            if pd.notnull(t1) and pd.notnull(t2):
                delta = abs((t1 - t2).total_seconds())
                if delta <= threshold_seconds:
                    results.append({
                        'bmkg_time': t1,
                        'usgs_time': t2,
                        'time_diff_s': delta,
                        'bmkg_mag': row1.mag,
                        'usgs_mag': row2.mag,
                        'bmkg_depth': row1.depth,
                        'usgs_depth': row2.depth,
                        'bmkg_lat': row1.lat,
                        'usgs_lat': row2.latitude,
                        'bmkg_lon': row1.lon,
                        'usgs_lon': row2.longitude,
                        'bmkg_evt_group': row1.evt_group,
                        'usgs_place': row2.place
                    })
    return pd.DataFrame(results)

# ✅ Call the function to generate the comparison DataFrame
df_comp = compare_events(df_rtsp_filtered, df_usgs_filtered, 'date_time', 'fix_dateusgs')

# 📋 Display the comparison
st.markdown("### 📊 Perbandingan Event RTSP vs USGS (berdasarkan waktu ±30s)")
st.dataframe(df_comp)


# 📊 Difference Metrics
df_tsp=df_comp.copy()
df_tsp['mag_diff'] = abs(df_tsp['bmkg_mag'] - df_tsp['usgs_mag'])
df_tsp['depth_diff'] = abs(df_tsp['bmkg_depth'] - df_tsp['usgs_depth'])
df_tsp['distance_diff_km'] = np.sqrt(
    degrees2kilometers(abs(df_tsp['bmkg_lon'] - df_tsp['usgs_lon'])) ** 2 +
    degrees2kilometers(abs(df_tsp['bmkg_lat'] - df_tsp['usgs_lat'])) ** 2
)

# 📈 Visuals
st.markdown("### 📉 Selisih Magnitudo USGS - BMKG")
st.line_chart(df_tsp, x="bmkg_time", y="mag_diff")

st.markdown("### 📉 Selisih Kedalaman USGS - BMKG")
st.line_chart(df_tsp, x="bmkg_time", y="depth_diff")

st.markdown("### 📉 Selisih Jarak USGS - BMKG")
st.line_chart(df_tsp, x="bmkg_time", y="distance_diff_km")

st.markdown("### 📋 Tabel Perbandingan Parameter Gempa USGS - BMKG")
st.dataframe(df_tsp)

# ⏱ Diseminasi Time
df_diss = fetch_dissemination_times(df_tsp['bmkg_evt_group'].dropna().unique())
st.markdown("### ⏱ Tabel Waktu Kirim OT vs Diseminasi RTSP BMKG")
st.dataframe(df_diss)
