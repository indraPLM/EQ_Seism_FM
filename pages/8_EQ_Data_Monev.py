# Earthquake Dashboard - Streamlit Desktop Edition
# Created by Indra Gunawan

import streamlit as st
import requests, numpy as np, pandas as pd, geopandas as gpd
from bs4 import BeautifulSoup
from PIL import Image
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
from cartopy.io.shapereader import Reader
import os
import re

# 🌍 Page Config
st.set_page_config(page_title='Earthquake Dashboard', layout='wide', page_icon='🌋')

# 🛠️ Sidebar Inputs
st.sidebar.header("Input Parameters")
time_start = st.sidebar.text_input('Start Time', '2025-06-01 00:00:00')
time_end = st.sidebar.text_input('End Time', '2025-06-30 23:59:59')
col1, col2 = st.sidebar.columns(2)
North = float(col1.text_input('North', '6.0'))
South = float(col2.text_input('South', '-13.0'))
col3, col4 = st.sidebar.columns(2)
West = float(col3.text_input('West', '90.0'))
East = float(col4.text_input('East', '142.0'))

# 📂 Load earthquake .txt file
file_path = './pages/bmkg_events_2019-2024.csv'


# Define expected column count (based on your table)
expected_columns = [
    'ID', 'DATE TIME A', 'DATE TIME B', 'MAG', 'TYPE', 'LAT', 'LON', 'DEPTH',
    'PHASE', 'AGENCY', 'STATUS', 'LOCATION A', 'LOCATION B'
]

# 🧵 Manual loader to handle trailing commas
data_rows = []
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip().rstrip(',')  # 🚫 Remove trailing comma
            if not line:
                continue
            parts = line.split(',')  # 📎 Use comma as delimiter
            if len(parts) == len(columns):
                data_rows.append(parts)
            else:
                st.warning(f"⚠️ Skipped line {line_num}: expected {len(columns)} columns, got {len(parts)}.")

except FileNotFoundError:
    st.error(f"🚫 File not found: {file_path}")
    st.stop()

# 🧾 Build and display DataFrame
if data_rows:
    df = pd.DataFrame(data_rows, columns=columns)
    st.success(f"✅ Loaded {len(df)} valid rows")
    st.dataframe(df.head())
else:
    st.warning("⚠️ No valid rows loaded — check for column formatting issues.")

# Optional: convert columns to proper types
df['MAG'] = pd.to_numeric(df['MAG'], errors='coerce')
df['DEPTH'] = pd.to_numeric(df['DEPTH'], errors='coerce')
df['LAT'] = pd.to_numeric(df['LAT'], errors='coerce')
df['LON'] = pd.to_numeric(df['LON'], errors='coerce')
df['DATE TIME A'] = pd.to_datetime(df['DATE TIME A'], errors='coerce')
df['DATE TIME B'] = pd.to_datetime(df['DATE TIME B'], errors='coerce')

st.dataframe(df)

# 🧹 Filter Data
df = df[
    (df['DATE TIME A'].between(time_start, time_end)) &
    (df['LAT'].between(South, North)) &
    (df['LON'].between(West, East))
]
st.dataframe(df)
# 📍 Load Island Shapefiles
def load_clip(name):
    return gpd.read_file(f"{name}_Area.shp")

def clip_df(df, island):
    geo_df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LON, df.LAT), crs="EPSG:4326")
    return geo_df.clip(load_clip(island))

# 📍 Convert to GeoDataFrame
gpd_seis = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LON, df.LAT), crs="EPSG:4326")

# 🔁 Island setup
list_pulau = ['Sumatra','Jawa','Bali-A','Nustra','Kalimantan','Sulawesi','Maluku','Papua']
list_color = ['r','g','b','y','c','m','purple','orange']
projection = ccrs.PlateCarree(central_longitude=120.0)

# 📦 Extract clipped coordinates per island
def get_eq_coords(pulau_name):
    try:
        polygon = gpd.read_file(f"{pulau_name}_Area.shp")
        clipped = gpd_seis.clip(polygon)
        a = np.array(clipped.LON)
        b = np.array(clipped.LAT)
        x, y, _ = projection.transform_points(ccrs.Geodetic(), a, b).T
        return x, y
    except Exception as e:
        st.warning(f"Gagal memproses data untuk {pulau_name}: {e}")
        return [], []

# 🖼️ Set up figure
fig = plt.figure(dpi=300)
ax = fig.add_subplot(111, projection=projection)
ax.set_extent((85, 145, -15, 10))

# 🌀 Plot per island
for i, pulau in enumerate(list_pulau):
    x, y = get_eq_coords(pulau)
    ax.scatter(x, y, s=5, color=list_color[i], marker="o", label=pulau, zorder=3)

    try:
        ax.add_geometries(
            Reader(f"{pulau}_Area.shp").geometries(),
            ccrs.PlateCarree(),
            facecolor="white",
            edgecolor=list_color[i],
            linewidth=0.5
        )
    except Exception as e:
        st.warning(f"Gagal memuat shapefile untuk {pulau}: {e}")

# 🗺️ Base map features
ax.add_feature(cartopy.feature.BORDERS, linestyle='-', linewidth=0.5, alpha=0.5)
ax.coastlines(resolution='10m', color='black', linestyle='-', linewidth=0.5, alpha=0.5)

# 📍 Custom legend below map
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label=list_pulau[i], markerfacecolor=list_color[i], markersize=8)
    for i in range(len(list_pulau))
]
ax.legend(handles=legend_elements,
          loc='lower center',
          bbox_to_anchor=(0.5, -0.25),
          ncol=4,
          frameon=False,
          fontsize='small')

# 📊 Show figure
st.markdown("### Seismisitas Berdasarkan Pulau")
st.pyplot(fig)

# 📉 Depth & Magnitude Stats
def stats(df):
    return [
        df[df.DEPTH < 60].shape[0],                         
        df[(df.DEPTH >= 60) & (df.DEPTH <= 300)].shape[0],
        df[df.DEPTH > 300].shape[0],                        
        df[df.MAG < 4].shape[0],                                
        df[(df.MAG >= 4) & (df.MAG < 5)].shape[0],               
        df[df.MAG >= 5].shape[0],                                
        df.shape[0]                                              
    ]

# 🔁 Compute Stats Per Island
regions = ['Sumatra','Jawa','Bali-A','Nustra','Kalimantan','Sulawesi','Maluku','Papua']
labels = ['SUMATRA','JAWA','BALI','NUSA TENGGARA','KALIMANTAN','SULAWESI','MALUKU','PAPUA']
stat_rows = [stats(clip_df(df, reg)) for reg in regions]
columns = ['<60 km','60–300 km','>300 km','M<4','M4–5','M≥5','Total']
stat_df = pd.DataFrame(stat_rows, columns=columns)
stat_df['Wilayah'] = labels
stat_df.set_index('Wilayah', inplace=True)

# 📊 Plot Stats by Island
st.subheader("📊 Depth & Magnitude by Island")
stat_df.drop(columns='Total').plot.bar(rot=6, figsize=(15,10))
plt.tight_layout()
plt.savefig("depth_mag.png")
st.image(Image.open("depth_mag.png"), caption="Depth & Magnitude per Island")

# 🧾 Table Summary
st.subheader("📋 Earthquake Summary per Island")
st.dataframe(stat_df)
