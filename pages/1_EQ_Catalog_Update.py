# -*- coding: utf-8 -*-
"""
Earthquake Dashboard - Streamlit Desktop Edition
Created by Indra Gunawan
"""
import streamlit as st
import requests, numpy as np, pandas as pd, geopandas as gpd
from bs4 import BeautifulSoup
from PIL import Image
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
from cartopy.io.shapereader import Reader

# Streamlit Config
st.set_page_config(page_title='🌍 Earthquake Catalog & Visualization', layout='wide')

# Sidebar Inputs
with st.sidebar:
    st.header("🛠️ Input Parameters")
    time_start = st.text_input('Start Time', '2025-01-01 00:00:00')
    time_end = st.text_input('End Time', '2025-01-31 23:59:59')
    col1, col2 = st.columns(2)
    North = float(col1.text_input('North', '6.0'))
    South = float(col2.text_input('South', '-13.0'))
    col3, col4 = st.columns(2)
    West = float(col3.text_input('West', '90.0'))
    East = float(col4.text_input('East', '142.0'))

# QC Catalog Fetch & Parse
@st.cache_data
def fetch_qc(url):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    rows = [line.split('|') for line in soup.p.text.split('\n') if line]
    cols = ['event_id','date_time','mode','status','phase','mag','type_mag',
            'n_mag','azimuth','rms','lat','lon','depth','type_event','remarks']
    df = pd.DataFrame([dict(zip(cols, row)) for row in rows[1:-2]])
    return df

df = fetch_qc("http://202.90.198.41/qc.txt")

# Coordinate Cleaning
def convert_coords(df):
    df['fixedLat'] = df['lat'].str.extract(r'([\d.]+)')[0].astype(float) * df['lat'].str.contains('S').apply(lambda x: -1 if x else 1)
    df['fixedLon'] = df['lon'].str.extract(r'([\d.]+)')[0].astype(float) * df['lon'].str.contains('W').apply(lambda x: -1 if x else 1)
    df['fixedDepth'] = df['depth'].str.replace('km', '').astype(float)
    df['mag'] = df['mag'].astype(float)
    df['sizemag'] = df['mag'] * 1000
    df['date_time'] = pd.to_datetime(df['date_time'])
    return df

df = convert_coords(df)

# Filtering
df = df[
    (df.date_time.between(time_start, time_end)) &
    (df.fixedLat.between(South, North)) &
    (df.fixedLon.between(West, East))
]

# Mapping
st.subheader("🗺️ Map of Earthquakes")
st.map(df, latitude="fixedLat", longitude="fixedLon", size="sizemag", zoom=3)

# Remarks Bar Chart
st.subheader("📊 Earthquake Frequency by Region")
df_count = df['remarks'].value_counts().reset_index()
df_count.columns = ['region','count']
df_count.plot.bar(x='region', y='count', rot=20, figsize=(20,12))
plt.xlabel("Region", fontsize=14)
plt.ylabel("Jumlah Gempa", fontsize=14)
plt.tight_layout()
plt.savefig('region_stats.png')
st.image(Image.open('region_stats.png'))

# Table Display
st.subheader("📋 Earthquake Catalog Table")
st.dataframe(df)
st.table(df_count)

# Island Clipping and Stats
@st.cache_data
def load_island(name):
    return gpd.read_file(f"{name}_Area.shp")

def clip_island(df, region):
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.fixedLon, df.fixedLat), crs="EPSG:4326")
    clip = gdf.clip(load_island(region))
    return clip

# Stats Function
def depth_mag_stats(df):
    stats = [
        df[df.fixedDepth < 60].shape[0],
        df[(df.fixedDepth >= 60) & (df.fixedDepth <= 300)].shape[0],
        df[df.fixedDepth > 300].shape[0],
        df[df.mag < 4].shape[0],
        df[(df.mag >= 4) & (df.mag < 5)].shape[0],
        df[df.mag >= 5].shape[0],
        df.shape[0]
    ]
    return stats

regions = ['Sumatra','Jawa','Bali-A','Nustra','Kalimantan','Sulawesi','Maluku','Papua']
colors = ['r','g','b','y','c','m','purple','orange']
stats_data = []

# Clip and Compile
for reg in regions:
    clip_df = clip_island(df, reg)
    stats_data.append(depth_mag_stats(clip_df))

headers = ['Dangkal <60','Menengah 60-300','Dalam >300','Kecil <4','Sedang 4-5','Besar ≥5','Total']
stats_df = pd.DataFrame(stats_data, columns=headers)
stats_df['Wilayah'] = ['SUMATRA','JAWA','BALI','NUSA TENGGARA','KALIMANTAN','SULAWESI','MALUKU','PAPUA']
stats_df.set_index('Wilayah', inplace=True)

# Plot per Island
st.subheader("📊 Depth & Magnitude by Island")
stats_df.drop(columns='Total').plot.bar(rot=6, figsize=(15,10))
plt.tight_layout()
plt.savefig('depth_mag_stats.png')
st.image(Image.open('depth_mag_stats.png'))

# Table Summary
st.subheader("📋 Regional Earthquake Statistics")
st.table(stats_df)
