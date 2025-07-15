# -*- coding: utf-8 -*-
"""
Streamlit app: Focal Mechanism Viewer (BMKG + Global CMT)
Created by: Indra Gunawan
"""
import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from obspy.imaging.beachball import beach
from bs4 import BeautifulSoup
import folium
from streamlit_folium import st_folium

# 🌍 Page Configuration
st.set_page_config(page_title="BMKG Focal Viewer", layout="wide", page_icon="🌋")

# 🛠️ Sidebar Inputs
st.sidebar.header("BMKG Focal Filter")
start_time = st.sidebar.text_input("Start Time", "2024-09-01 00:00:00")
end_time = st.sidebar.text_input("End Time", "2025-01-31 23:59:59")
col1, col2 = st.sidebar.columns(2)
North = float(col1.text_input("North", "6.0"))
South = float(col2.text_input("South", "-13.0"))
col3, col4 = st.sidebar.columns(2)
West = float(col3.text_input("West", "90.0"))
East = float(col4.text_input("East", "142.0"))

# 🧹 Coordinate Conversion
def fix_coord(val, axis):
    val = val.strip()
    if axis == 'lat':
        return -float(val.strip('S')) if val.endswith('S') else float(val.strip('N'))
    if axis == 'lon':
        return -float(val.strip('W')) if val.endswith('W') else float(val.strip('E'))

def fix_float(col): return pd.to_numeric(col, errors='coerce')

# 📦 Function to fetch and parse HTML catalog
@st.cache_data(show_spinner=False)
@st.cache_data(show_spinner=False)
def load_bmkg_focal(url):
    res = requests.get(url)
    lines = res.text.strip().split('\n')
    rows = [line.split('|') for line in lines if line]
    return rows

url = "http://202.90.198.41/qc_focal.txt" 
rows = load_bmkg_focal(url) 
print(rows) 

# 🧾 Build DataFrame 
base_cols = ['event_id', 'mode', 'status', 'mag', 'type_mag',
             'lat', 'lon', 'depth', 'S1', 'D1', 'R1', 'S2', 'D2', 'R2'] 
n_extra = max(0, len(rows[0]) - len(base_cols)) if rows else 0 
cols = base_cols + [f'extra_{i}' for i in range(n_extra)] 
df = pd.DataFrame(rows[1:], columns=cols) 
st.dataframe(df)

# 🔄 Convert columns
df['fixedLat'] = df['lat'].apply(lambda x: fix_coord(x, 'lat'))
df['fixedLon'] = df['lon'].apply(lambda x: fix_coord(x, 'lon'))
df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')
for col in ['mag','depth','S1','D1','R1','S2','D2','R2']: df[col] = fix_float(df[col])

# 📋 Filter Data
df = df[
    (df['date_time'] >= start_time) & (df['date_time'] <= end_time) &
    (df['fixedLat'].between(South, North)) &
    (df['fixedLon'].between(West, East))
]

st.markdown("### 🧭 Static Focal Mechanism Plot (Cartopy Beachballs)")

# 🗺️ Cartopy Beachball Plot
proj = ccrs.PlateCarree(central_longitude=120)
fig = plt.figure(dpi=300)
ax = fig.add_subplot(111, projection=proj)
ax.set_extent((West, East, South-0.5, North+0.5))
ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, alpha=0.5)
ax.coastlines(resolution='10m', color='black', linewidth=0.5, alpha=0.5)

for _, row in df.iterrows():
    x, y = proj.transform_point(row["fixedLon"], row["fixedLat"], src_crs=ccrs.Geodetic())
    color = "r" if row["depth"] < 60 else "y" if row["depth"] < 300 else "g"
    ball = beach([row["S1"], row["D1"], row["R1"]],
                 xy=(x, y), width=0.5, linewidth=0.5,
                 alpha=0.65, zorder=10, facecolor=color)
    ax.add_collection(ball)

st.pyplot(fig)

# 🌐 Folium Interactive Plot
st.markdown("### 🌎 Interactive Map with HTML Popups (Folium)")

map_center = [(South + North)/2, (West + East)/2]
m = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB positron")

for _, row in df.iterrows():
    depth = row["depth"]
    color = "red" if depth < 60 else "orange" if depth < 300 else "green"

    html_popup = f"""
    <div style="font-family:Arial; font-size:13px">
        <b>ID:</b> {row['event_id']}<br>
        <b>Date:</b> {row['date_time'].strftime('%Y-%m-%d %H:%M:%S')}<br>
        <b>Magnitude:</b> {row['mag']} ML<br>
        <b>Depth:</b> {depth:.1f} km<br>
        <b>Lat/Lon:</b> ({row['fixedLat']:.2f}, {row['fixedLon']:.2f})<br><br>
        <b>Focal Mechanism:</b><br>
        Strike1: {row['S1']}° &nbsp; Dip1: {row['D1']}° &nbsp; Rake1: {row['R1']}°<br>
        Strike2: {row['S2']}° &nbsp; Dip2: {row['D2']}° &nbsp; Rake2: {row['R2']}°
    </div>
    """

    folium.CircleMarker(
        location=[row["fixedLat"], row["fixedLon"]],
        radius=4,
        color=color,
        fill=True,
        fill_opacity=0.8,
        popup=folium.Popup(html_popup, max_width=350)
    ).add_to(m)

st_folium(m, width=900, height=600)

# 🧾 Display Catalog
st.markdown("### 📋 BMKG Focal Catalog Table")
st.dataframe(df)

# 🌐 Global CMT Section
st.markdown("### 🌎 Peta Global CMT Harvard")
def load_cmt(url):
    txt = requests.get(url).text
    lines = txt.split("\n")
    records = [lines[i:i+5] for i in range(0, len(lines), 5)]
    rows = []
    for rec in records:
        if len(rec) < 5: continue
        dt = f"{rec[0][5:15]} {rec[0][16:21]}"
        row = {
            'Datetime': dt,
            'Lat': float(rec[0][26:33]),
            'Lon': float(rec[0][35:41]),
            'Depth': float(rec[0][43:47]),
            'Mag_mb': float(rec[0][47:51]),
            'Mag_Ms': float(rec[0][52:55]),
            'S1': float(rec[4][56:60]),
            'D1': float(rec[4][61:64]),
            'R1': float(rec[4][65:69])
        }
        rows.append(row)
    return pd.DataFrame(rows)

urls = [
    "https://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/jan76_dec20.ndk",
    "https://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/PRE1976/deep_1962-1976.ndk",
    "https://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/PRE1976/intdep_1962-1975.ndk"
]

df_cmt = pd.concat([load_cmt(url) for url in urls])
df_cmt['Datetime'] = pd.to_datetime(df_cmt['Datetime'], errors='coerce')
df_cmt = df_cmt[
    (df_cmt['Datetime'] >= cmt_start) & (df_cmt['Datetime'] <= cmt_end) &
    (df_cmt['Lat'].between(south, north)) & (df_cmt['Lon'].between(west, east))
]

# 🗺️ Plot Global CMT
fig2 = plt.figure(dpi=300)
ax2 = fig2.add_subplot(111, projection=ccrs.PlateCarree(central_longitude=120))
ax2.set_extent((west, east, south-0.5, north+0.5))
ax2.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, alpha=0.5)
ax2.coastlines(resolution='10m', color='black', linewidth=0.5, alpha=0.5)
draw_beachballs(df_cmt, ax2, ax2.projection, depth_col='Depth', lon_col='Lon', lat_col='Lat')
st.pyplot(fig2)
st.dataframe(df_cmt)
