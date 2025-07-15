# -*- coding: utf-8 -*-
"""
Streamlit App: BMKG Focal Mechanism Viewer with Summary and Beachball Export
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
from io import BytesIO
import base64
import folium
from streamlit_folium import st_folium

# 🌍 Page config
st.set_page_config(page_title="BMKG Focal Viewer", layout="wide", page_icon="🌋")

# 🛠 Sidebar Inputs
st.sidebar.header("BMKG Focal Filter")
start_time = st.sidebar.text_input("Start Time", "2024-09-01 00:00:00")
end_time = st.sidebar.text_input("End Time", "2025-01-31 23:59:59")
col1, col2 = st.sidebar.columns(2)
North = float(col1.text_input("North", "6.0"))
South = float(col2.text_input("South", "-13.0"))
col3, col4 = st.sidebar.columns(2)
West = float(col3.text_input("West", "90.0"))
East = float(col4.text_input("East", "142.0"))

# 📦 Fetch BMKG catalog
@st.cache_data
def load_bmkg_focal(url):
    res = requests.get(url)
    raw_text = res.text.strip()
    lines = raw_text.split("\n")
    rows = [line.split("|") for line in lines if "|" in line]
    return rows


url = "http://202.90.198.41/qc_focal.txt"
rows = load_bmkg_focal(url)

base_cols = ['date_time', 'mode', 'status', 'phase', 'mag', 'type_mag','count','azgap','RMS',
             'lat', 'lon', 'depth', 'S1', 'D1', 'R1', 'S2', 'D2', 'R2','Fit','DC','CLVD','type','location']
n_extra = max(0, len(rows[0]) - len(base_cols)) if rows else 0
cols = base_cols + [f'extra_{i}' for i in range(n_extra)]
df = pd.DataFrame(rows[1:], columns=cols)

# 🔁 Preprocess columns
def fix_coord(val, axis):
    val = val.strip()
    return -float(val.strip('S')) if val.endswith('S') else float(val.strip('N')) if axis == 'lat' else \
           -float(val.strip('W')) if val.endswith('W') else float(val.strip('E'))

def fix_float(col): return pd.to_numeric(col, errors='coerce')

df['fixedLat'] = df['lat'].apply(lambda x: fix_coord(x, 'lat'))
df['fixedLon'] = df['lon'].apply(lambda x: fix_coord(x, 'lon'))
df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')
for col in ['mag','depth','S1','D1','R1','S2','D2','R2']: df[col] = fix_float(df[col])

df = df[
    (df['date_time'] >= start_time) & (df['date_time'] <= end_time) &
    (df['fixedLat'].between(South, North)) &
    (df['fixedLon'].between(West, East))
]

# 🎯 Beachball image encoder
def beachball_base64(S, D, R):
    if pd.isnull(S) or pd.isnull(D) or pd.isnull(R): return None
    if not (0 <= D <= 90 and -180 <= R <= 180): return None
    fig, ax = plt.subplots(figsize=(1.2, 1.2), dpi=100)
    ax.set_xlim(-100, 100); ax.set_ylim(-100, 100); ax.axis("off")
    ball = beach([S, D, R], xy=(0, 0), width=90, linewidth=1, facecolor="black")
    ax.add_collection(ball)
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0); plt.close(fig)
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f'<img src="data:image/png;base64,{encoded}" width="70"/>'

# 🧾 Seismic Summary Table
st.markdown("### 📋 Seismic Event Table with Beachball Diagrams")

def safe(val, precision=None):
    if pd.isnull(val):
        return "—"
    if isinstance(val, float) and precision is not None:
        return f"{val:.{precision}f}"
    return str(val)



table_rows = []
csv_rows = []
for i, row in df.iterrows():
    img = beachball_base64(row["S1"], row["D1"], row["R1"])
    table_rows.append(f"""
    <tr>
        <td>{i+1}</td>
        <td>{safe(row['date_time'].date())}</td>
        <td>{safe(row['date_time'].time())}</td>
        <td>{safe(row['mag'], 1)}</td>
        <td>{safe(row['lat'], 2)}°</td>
        <td>{safe(row['lon'], 2)}°</td>
        <td>{safe(row['depth'])} km</td>
        <td>{safe(row['S1'])} / {safe(row['D1'])} / {safe(row['R1'])}</td>
        <td>{safe(row['location'])}</td>
        <td>{img if img else '<i>Invalid</i>'}</td>
    </tr>
    """)

    # Add CSV row with raw image (encoded or placeholder)
    csv_rows.append({
        'date_time': row['date_time'],
        'lat': row['lat'],
        'lon': row['lon'],
        'depth': row['depth'],
        'mag': row['mag'],
        'S1': row['S1'],
        'D1': row['D1'],
        'R1': row['R1'],
        'S2': row['S2'],
        'D2': row['D2'],
        'R2': row['R2'],
        'location': row['location'],
        'beachball_image': img if img else 'Invalid'
    })

html_table = f"""
<table border="1" style="border-collapse:collapse; text-align:center; font-family:Arial; font-size:12px">
<thead>
    <tr>
        <th>No</th><th>Date</th><th>Time</th><th>Mag</th><th>Lat</th><th>Lon</th>
        <th>Depth</th><th>S/D/R</th><th>Location</th><th>Focal Mechanism</th>
    </tr>
</thead>
<tbody>
    {''.join(table_rows)}
</tbody>
</table>
"""
st.markdown(html_table, unsafe_allow_html=True)

# 📥 Download CSV with encoded image as string
st.markdown("### 📥 Download Summary CSV")
df_export = pd.DataFrame(csv_rows)
csv = df_export.to_csv(index=False)
st.download_button("Download Focal Summary CSV", csv, file_name="focal_summary.csv", mime="text/csv")

# 🗺️ Cartopy Plot
st.markdown("### 🗺️ Static Beachball Plot (Cartopy)")
fig = plt.figure(dpi=300)
ax = fig.add_subplot(111, projection=ccrs.PlateCarree(central_longitude=120))
ax.set_extent((West, East, South-0.5, North+0.5))
ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, alpha=0.5)
ax.coastlines(resolution='10m', color='black', linewidth=0.5, alpha=0.5)
for _, row in df.iterrows():
    if pd.notnull(row["S1"]) and pd.notnull(row["D1"]) and pd.notnull(row["R1"]):
        x, y = ax.projection.transform_point(row["fixedLon"], row["fixedLat"], ccrs.Geodetic())
        color = "r" if row["depth"] < 60 else "y" if row["depth"] < 300 else "g"
        ball = beach([row["S1"], row["D1"], row["R1"]],
                     xy=(x, y), width=1.5, linewidth=0.5,
                     alpha=0.65, zorder=10, facecolor=color)
        ax.add_collection(ball)
st.pyplot(fig)


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
