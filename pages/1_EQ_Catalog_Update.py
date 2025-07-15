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

# 🌍 Page Config
st.set_page_config(page_title='Earthquake Dashboard', layout='wide', page_icon='🌋')

# 🛠️ Sidebar Inputs
st.sidebar.header("Input Parameters")
time_start = st.sidebar.text_input('Start Time', '2025-01-01 00:00:00')
time_end = st.sidebar.text_input('End Time', '2025-01-31 23:59:59')
col1, col2 = st.sidebar.columns(2)
North = float(col1.text_input('North', '6.0'))
South = float(col2.text_input('South', '-13.0'))
col3, col4 = st.sidebar.columns(2)
West = float(col3.text_input('West', '90.0'))
East = float(col4.text_input('East', '142.0'))

# 🔎 Load Earthquake Catalog (with robust HTML fallback)
@st.cache_data(show_spinner=False)
def fetch_qc(url):
    try:
        response = requests.get(url)
        text = response.text.strip()
        if "|" in text:
            rows = [line.split('|') for line in text.split('\n') if line]
        else:
            soup = BeautifulSoup(text, 'html.parser')
            if soup.p and soup.p.text:
                rows = [line.split('|') for line in soup.p.text.split('\n') if line]
            else:
                return pd.DataFrame()
        columns = ['event_id','date_time','mode','status','phase','mag','type_mag',
                   'n_mag','azimuth','rms','lat','lon','depth','type_event','remarks']
        return pd.DataFrame([dict(zip(columns, row)) for row in rows[1:-2]])
    except Exception:
        return pd.DataFrame()

df = fetch_qc("http://202.90.198.41/qc.txt")
if df.empty:
    st.error("⚠️ Failed to retrieve or parse earthquake data from source.")
    st.stop()

# 🔄 Data Cleaning & Conversion
def preprocess(df):
    df['fixedLat'] = df['lat'].str.extract(r'([\d.]+)').astype(float) * df['lat'].str.contains('S').apply(lambda x: -1 if x else 1)
    df['fixedLon'] = df['lon'].str.extract(r'([\d.]+)').astype(float) * df['lon'].str.contains('W').apply(lambda x: -1 if x else 1)
    df['fixedDepth'] = df['depth'].str.replace('km','').astype(float)
    df['mag'] = df['mag'].astype(float)
    df['date_time'] = pd.to_datetime(df['date_time'])
    df['sizemag'] = df['mag'] * 1000
    return df

df = preprocess(df)

# 🧹 Filter Data
df = df[
    (df.date_time.between(time_start, time_end)) &
    (df.fixedLat.between(South, North)) &
    (df.fixedLon.between(West, East))
]

# 🗺️ Plot Map
st.subheader("🗺️ Earthquake Map")
st.map(df, latitude="fixedLat", longitude="fixedLon", size="sizemag", zoom=3)

# 📊 Remarks Chart
st.subheader("📊 Frequency by Region")
remarks = df['remarks'].value_counts().reset_index()
remarks.columns = ['Region', 'Count']
remarks.plot.bar(x='Region', y='Count', figsize=(20,12), rot=20)
plt.xlabel("Region")
plt.ylabel("Earthquake Count")
plt.tight_layout()
plt.savefig("region_freq.png")
st.image(Image.open("region_freq.png"), caption="Frequency by Region")

# 📋 Display Table
st.subheader("📋 Earthquake Catalog")
st.dataframe(df)
st.table(remarks)

# 📍 Load Island Shapefiles
def load_clip(name):
    return gpd.read_file(f"{name}_Area.shp")

def clip_df(df, island):
    geo_df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.fixedLon, df.fixedLat), crs="EPSG:4326")
    return geo_df.clip(load_clip(island))

# 📉 Depth & Magnitude Stats
def stats(df):
    return [
        df[df.fixedDepth < 60].shape[0],                         # Dangkal
        df[(df.fixedDepth >= 60) & (df.fixedDepth <= 300)].shape[0],  # Menengah
        df[df.fixedDepth > 300].shape[0],                        # Dalam
        df[df.mag < 4].shape[0],                                 # Kecil
        df[(df.mag >= 4) & (df.mag < 5)].shape[0],               # Sedang
        df[df.mag >= 5].shape[0],                                # Besar
        df.shape[0]                                              # Total
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
st.table(stat_df)
