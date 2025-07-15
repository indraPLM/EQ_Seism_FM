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

# 🌍 Page Config
st.set_page_config(page_title="Peta Focal Mechanism", layout="wide", page_icon="🌋")

# 🎛️ Sidebar Filters
def get_bounds(prefix=""):
    st.sidebar.header(f"{prefix} Parameter")
    col1, col2 = st.sidebar.columns(2)
    north = float(col1.text_input("North", "6.0"))
    south = float(col2.text_input("South", "-13.0"))
    col3, col4 = st.sidebar.columns(2)
    west = float(col3.text_input("West", "90.0"))
    east = float(col4.text_input("East", "142.0"))
    t_start = st.sidebar.text_input("Start Time", "2024-09-01 00:00:00" if prefix == "Focal BMKG" else "2000-01-01 00:00")
    t_end = st.sidebar.text_input("End Time", "2025-01-31 23:59:59" if prefix == "Focal BMKG" else "2020-12-31 23:59")
    return t_start, t_end, west, east, south, north

bmkg_start, bmkg_end, west, east, south, north = get_bounds("Focal BMKG")
cmt_start, cmt_end, *_ = get_bounds("Global CMT")

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
fig1 = plt.figure(dpi=300)
ax1 = fig1.add_subplot(111, projection=ccrs.PlateCarree(central_longitude=120))
ax1.set_extent((west, east, south-0.5, north+0.5))
ax1.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, alpha=0.5)
ax1.coastlines(resolution='10m', color='black', linewidth=0.5, alpha=0.5)
draw_beachballs(df_bmkg, ax1, ax1.projection)
st.pyplot(fig1)
st.dataframe(df_bmkg)

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
