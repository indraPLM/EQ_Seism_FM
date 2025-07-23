# Earthquake Dashboard - Streamlit Desktop Edition
# Created by Indra Gunawan

import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
from cartopy.io.shapereader import Reader
from matplotlib.lines import Line2D
from PIL import Image
import os

# 🌍 Page Config
st.set_page_config(page_title='Earthquake Dashboard', layout='wide', page_icon='🌋')

# 🛠️ Sidebar Inputs
st.sidebar.header("Input Parameters")
time_start = st.sidebar.text_input('Start Time', '2024-01-01 00:00:00')
time_end   = st.sidebar.text_input('End Time', '2024-03-30 23:59:59')
col1, col2 = st.sidebar.columns(2)
North = float(col1.text_input('North', '6.0'))
South = float(col2.text_input('South', '-13.0'))
col3, col4 = st.sidebar.columns(2)
West  = float(col3.text_input('West', '90.0'))
East  = float(col4.text_input('East', '142.0'))

# 📂 Load and Clean Data
file_path = './pages/event_jan-mar_2024_cleaned.csv'
# Robust CSV loading with header fallback
try:
    df_raw = pd.read_csv(file_path, header=None)
except Exception as e:
    st.error(f"❌ Failed to read CSV: {e}")
    st.stop()

# Promote first row to header
df_raw.columns = df_raw.iloc[0]
df = df_raw[1:].copy()

# Convert necessary columns to correct types
for col in ['DATE', 'MAG', 'DEPTH', 'LAT', 'LON']:
    if col in df.columns:
        if col == 'DATE':
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    else:
        st.error(f"⚠️ Column '{col}' not found in data. Please check formatting.")
        st.stop()

# 🧹 Filter Data
df_filtered = df[
    (df['DATE'].between(time_start, time_end)) &
    (df['LAT'].between(South, North)) &
    (df['LON'].between(West, East))
]

st.subheader("📋 Filtered Earthquake Events")
st.dataframe(df_filtered)

# 🗺️ Island Setup
list_pulau = ['Sumatra','Jawa','Bali-A','Nustra','Kalimantan','Sulawesi','Maluku','Papua']
list_color = ['r','g','b','y','c','m','purple','orange']
labels     = ['SUMATRA','JAWA','BALI','NUSA TENGGARA','KALIMANTAN','SULAWESI','MALUKU','PAPUA']
projection = ccrs.PlateCarree(central_longitude=120.0)

# 📍 Island Functions
def load_clip(name):
    return gpd.read_file(f"{name}_Area.shp")

def clip_df(df, island):
    geo_df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LON, df.LAT), crs="EPSG:4326")
    return geo_df.clip(load_clip(island))

gpd_seis = gpd.GeoDataFrame(df_filtered, geometry=gpd.points_from_xy(df_filtered.LON, df_filtered.LAT), crs="EPSG:4326")

def get_eq_coords(pulau_name):
    try:
        polygon = gpd.read_file(f"{pulau_name}_Area.shp")
        clipped = gpd_seis.clip(polygon)
        x, y, _ = projection.transform_points(ccrs.Geodetic(), np.array(clipped.LON), np.array(clipped.LAT)).T
        return x, y
    except Exception as e:
        st.warning(f"Gagal memproses {pulau_name}: {e}")
        return [], []

# 🖼️ Plot Earthquake Map
fig = plt.figure(dpi=300)
ax = fig.add_subplot(111, projection=projection)
ax.set_extent((85, 145, -15, 10))

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
    except:
        continue

ax.add_feature(cartopy.feature.BORDERS, linestyle='-', linewidth=0.5, alpha=0.5)
ax.coastlines(resolution='10m', color='black', linestyle='-', linewidth=0.5, alpha=0.5)

legend_elements = [
    Line2D([0], [0], marker='o', color='w', label=labels[i], markerfacecolor=list_color[i], markersize=8)
    for i in range(len(list_pulau))
]
ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=4, frameon=False, fontsize='small')

st.markdown("### 🗺️ Seismic Events by Island")
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

stat_rows = [stats(clip_df(df_filtered, reg)) for reg in list_pulau]
stat_df = pd.DataFrame(stat_rows, columns=['<60 km','60–300 km','>300 km','M<4','M4–5','M≥5','Total'])
stat_df['Wilayah'] = labels
stat_df.set_index('Wilayah', inplace=True)

st.subheader("📊 Depth & Magnitude by Island")
stat_df.drop(columns='Total').plot.bar(rot=6, figsize=(15,10))
plt.tight_layout()
plt.savefig("depth_mag.png")
st.image(Image.open("depth_mag.png"), caption="Depth & Magnitude per Island")

st.subheader("📋 Earthquake Summary per Island")
st.dataframe(stat_df)
