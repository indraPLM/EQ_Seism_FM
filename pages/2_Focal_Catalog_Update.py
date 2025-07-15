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

# 🌍 Streamlit config
st.set_page_config(page_title="Focal Mechanism Viewer", layout="wide", page_icon="🌋")

# 🛠️ Sidebar input: BMKG
st.sidebar.header("BMKG Parameter")
bmkg_start = st.sidebar.text_input("Start Time", "2024-09-01 00:00:00", key="bmkg_start")
bmkg_end = st.sidebar.text_input("End Time", "2025-01-31 23:59:59", key="bmkg_end")
bmkg_col1, bmkg_col2 = st.sidebar.columns(2)
bmkg_North = float(bmkg_col1.text_input("North", "6.0", key="bmkg_north"))
bmkg_South = float(bmkg_col2.text_input("South", "-13.0", key="bmkg_south"))
bmkg_col3, bmkg_col4 = st.sidebar.columns(2)
bmkg_West = float(bmkg_col3.text_input("West", "90.0", key="bmkg_west"))
bmkg_East = float(bmkg_col4.text_input("East", "142.0", key="bmkg_east"))

# 📡 Sidebar input: Global CMT
st.sidebar.header("Global CMT Parameter")
cmt_start = st.sidebar.text_input("Start Time", "2000-01-01 00:00", key="cmt_start")
cmt_end = st.sidebar.text_input("End Time", "2020-12-31 23:59", key="cmt_end")
cmt_col1, cmt_col2 = st.sidebar.columns(2)
cmt_North = float(cmt_col1.text_input("North", "6.0", key="cmt_north"))
cmt_South = float(cmt_col2.text_input("South", "-13.0", key="cmt_south"))
cmt_col3, cmt_col4 = st.sidebar.columns(2)
cmt_West = float(cmt_col3.text_input("West", "90.0", key="cmt_west"))
cmt_East = float(cmt_col4.text_input("East", "142.0", key="cmt_east"))


# 🔄 Utility Functions
def fix_coord(val, pos='lat'):
    val = val.strip()
    if pos == 'lat':
        return -float(val.strip('S')) if val.endswith('S') else float(val.strip('N'))
    else:
        return -float(val.strip('W')) if val.endswith('W') else float(val.strip('E'))

def fix_float(col): return pd.to_numeric(col, errors='coerce')

def draw_beachballs(df, ax, proj, depth_col='depth', s_col='S1', d_col='D1', r_col='R1', lon_col='fixedLon', lat_col='fixedLat'):
    for _, row in df.iterrows():
        x, y = proj.transform_point(row[lon_col], row[lat_col], src_crs=ccrs.Geodetic())
        width = 0.5
        color = 'r' if row[depth_col] < 60 else 'y' if row[depth_col] < 300 else 'g'
        mech = [row[s_col], row[d_col], row[r_col]]
        ball = beach(mech, xy=(x, y), width=width, linewidth=0.5, alpha=0.65, zorder=10, facecolor=color)
        ax.add_collection(ball)

# 📡 BMKG Section
st.markdown("### 🧭 Peta Focal Mechanism BMKG")
bmkg_url = "http://202.90.198.41/qc_focal.txt"
response = requests.get(bmkg_url)
soup = BeautifulSoup(response.text, "html.parser")
raw_lines = soup.p.text.split("\n") if soup.p else []
entries = [line.split("|") for line in raw_lines if line]

cols = ['event_id', 'date_time', 'date_create', 'mode', 'status', 'mag', 'type_mag',
        'lat', 'lon', 'depth', 'S1', 'D1', 'R1', 'S2', 'D2', 'R2'] + ['...'] * (len(entries[0]) - 16)
df_bmkg = pd.DataFrame(entries[1:], columns=cols)
df_bmkg['fixedLat'] = df_bmkg['lat'].apply(lambda x: fix_coord(x, 'lat'))
df_bmkg['fixedLon'] = df_bmkg['lon'].apply(lambda x: fix_coord(x, 'lon'))
df_bmkg['date_time'] = pd.to_datetime(df_bmkg['date_time'], errors='coerce')
for col in ['mag','depth','S1','D1','R1']: df_bmkg[col] = fix_float(df_bmkg[col])
df_bmkg = df_bmkg[
    (df_bmkg['date_time'] >= bmkg_start) & (df_bmkg['date_time'] <= bmkg_end) &
    (df_bmkg['fixedLat'].between(south, north)) & (df_bmkg['fixedLon'].between(west, east))
]

# 🗺️ Plot BMKG Focal Mechanisms
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from obspy.imaging.beachball import beach

# Set up projection
projection = ccrs.PlateCarree(central_longitude=120)
fig = plt.figure(dpi=300)
ax = fig.add_subplot(111, projection=projection)
ax.set_extent((West, East, South-0.5, North+0.5))
ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, alpha=0.5)
ax.coastlines(resolution='10m', color='black', linewidth=0.5, alpha=0.5)

# Plot beachballs
for _, row in df_bmkg.iterrows():
    x, y = projection.transform_point(row['fixedLon'], row['fixedLat'], src_crs=ccrs.Geodetic())
    color = 'r' if row['depth'] < 60 else 'y' if row['depth'] < 300 else 'g'
    ball = beach([row['S1'], row['D1'], row['R1']], xy=(x, y), width=0.5, facecolor=color,
                 linewidth=0.5, alpha=0.65, zorder=10)
    ax.add_collection(ball)

st.markdown("### 🎯 Visualisasi Statis dengan Cartopy")
st.pyplot(fig)
st.dataframe(df_bmkg)

from streamlit_folium import st_folium

# Create Folium map
center_lat, center_lon = (South + North) / 2, (West + East) / 2
m = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles='CartoDB positron')

# Add markers for BMKG focal mechanism events
for _, row in df_bmkg.iterrows():
    depth = row['depth']
    color = 'red' if depth < 60 else 'orange' if depth < 300 else 'green'
    popup_text = f"ID: {row['event_id']}<br>Mag: {row['mag']}<br>Depth: {depth} km"
    folium.CircleMarker(
        location=[row['fixedLat'], row['fixedLon']],
        radius=4,
        color=color,
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

st.markdown("### 🧭 Visualisasi Interaktif dengan Folium")
st_folium(m, width=900, height=600)


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
