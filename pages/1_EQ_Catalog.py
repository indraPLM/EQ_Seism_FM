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
import datetime

# 🌍 Page Config
st.set_page_config(page_title='Earthquake Dashboard', layout='wide', page_icon='🌋')

# 🛠️ Sidebar Inputs
st.sidebar.header("Input Parameters")
tim_end_def = datetime.datetime.now()
tim_sta_def = tim_end_def - datetime.timedelta(days=30)
tim_sta = st.sidebar.datetime_input("Start Date", tim_sta_def)
tim_end = st.sidebar.datetime_input("End Date", tim_end_def)
col1, col2 = st.sidebar.columns(2)
North = float(col1.text_input('North', '6.0'))
South = float(col2.text_input('South', '-13.0'))
col3, col4 = st.sidebar.columns(2)
West = float(col3.text_input('West', '90.0'))
East = float(col4.text_input('East', '142.0'))
col5, col6 = st.sidebar.columns(2)
Mmin = float(col5.text_input('Min Mag.', '5.0'))
Mmax = float(col6.text_input('Max Mag', '9.0'))

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
    lat_num = df['lat'].str.extract(r'([\d.]+)')[0].astype(float)
    lat_sign = df['lat'].str.contains('S').apply(lambda x: -1 if x else 1)
    df['fixedLat'] = lat_num * lat_sign

    lon_num = df['lon'].str.extract(r'([\d.]+)')[0].astype(float)
    lon_sign = df['lon'].str.contains('W').apply(lambda x: -1 if x else 1)
    df['fixedLon'] = lon_num * lon_sign

    df['fixedDepth'] = df['depth'].str.replace('km', '').astype(float)
    df['mag'] = df['mag'].astype(float)
    df['sizemag'] = df['mag'] * 1000
    df['date_time'] = pd.to_datetime(df['date_time'])

    return df


df = preprocess(df)

# 🧹 Filter Data
df = df[
    (df.date_time.between(tim_sta, tim_end)) &
    (df.fixedLat.between(South, North)) &
    (df.mag.between(Mmin,Mmax)) &
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
df = df.sort_values(by='date_time')
df.index = range(1, len(df) + 1)
st.dataframe(df)
st.table(remarks)
summary_df=df.copy()
#columns = ['event_id','date_time','mode','status','phase','mag','type_mag',
#                   'n_mag','azimuth','rms','lat','lon','depth','type_event','remarks']

#summary_df.columns = ['Tanggal','Waktu','Magnitude','Type Magnitude','Latitude','Longitude','Depth',
#                      'Strike NP1','Dip NP1','Rake NP1','Strike NP2','Dip NP2','Rake NP2','Remark']
#summary_df.index = range(1, len(summary_df)+1)
#st.dataframe(summary_df)

# 🔢 Magnitude Classification
def classify_mag(mag):
    if mag < 5:
        return '<5'
    elif 5 <= mag < 6:
        return '5–6'
    elif 6 <= mag < 7:
        return '6–7'
    else:
        return '≥7'

df['mag_class'] = df['mag'].apply(classify_mag)

# 🧮 Count Frequency by Region and Magnitude Class
region_mag_freq = df.groupby(['remarks', 'mag_class']).size().unstack(fill_value=0)

# ✨ Ensure consistent column order and fill missing ones
expected_cols = ['<5', '5–6', '6–7', '≥7']
for col in expected_cols:
    if col not in region_mag_freq.columns:
        region_mag_freq[col] = 0
region_mag_freq = region_mag_freq[expected_cols]

# 🎨 Plot Bar Chart
color_map = {'<5': 'blue', '5–6': 'red', '6–7': 'green', '≥7': 'yellow'}
region_mag_freq.plot(kind='bar', stacked=False, figsize=(20, 12), color=[color_map[col] for col in expected_cols])

plt.title("Earthquake Frequency by Region and Magnitude Category")
plt.xlabel("Region")
plt.ylabel("Number of Earthquakes")
plt.xticks(rotation=45)
plt.tight_layout()

# 📸 Export and Render Chart
plt.savefig("region_mag_bar.png")
st.subheader("📊 Frequency by Region and Magnitude Category")
st.image("region_mag_bar.png", caption="Frequency by Region and Magnitude Classification")

# 📋 Show Frequency DataFrame
st.subheader("📋 Earthquake Frequency by Region and Magnitude Class")
st.dataframe(region_mag_freq)

# 📊 Frequency totals per magnitude class
mag_totals = region_mag_freq.sum()
labels = mag_totals.index
sizes = mag_totals.values
colors = ['blue', 'red', 'green', 'yellow']
explode = [0.05]*len(sizes)  # slightly "explode" all slices for effect

import plotly.graph_objects as go

# 🧮 Total frequency across all magnitude categories
mag_totals = region_mag_freq.sum()
labels = mag_totals.index
values = mag_totals.values
colors = ['blue', 'red', 'green', 'yellow']

# 🥧 3D-style Pie Chart with Plotly
fig_pie = go.Figure(
    data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.3,
        pull=[0.05]*len(values),
        textinfo='label+percent',
        textfont=dict(size=14),
        showlegend=False
    )]
)

fig_pie.update_layout(
    title="Magnitude Classification Distribution",
    height=600
)

# 🎯 Display in Streamlit
st.subheader("🥧 Magnitude Class Distribution (3D Style)")
st.plotly_chart(fig_pie, use_container_width=True)

# 📍 Load Island Shapefiles
def load_clip(name):
    return gpd.read_file(f"{name}_Area.shp")

def clip_df(df, island):
    geo_df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.fixedLon, df.fixedLat), crs="EPSG:4326")
    return geo_df.clip(load_clip(island))

# 📍 Convert to GeoDataFrame
gpd_seis = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.fixedLon, df.fixedLat), crs="EPSG:4326")

# 🔁 Island setup
list_pulau = ['Sumatra','Jawa','Bali-A','Nustra','Kalimantan','Sulawesi','Maluku','Papua']
list_color = ['r','g','b','y','c','m','purple','orange']
projection = ccrs.PlateCarree(central_longitude=120.0)

# 📦 Extract clipped coordinates per island
def get_eq_coords(pulau_name):
    try:
        polygon = gpd.read_file(f"{pulau_name}_Area.shp")
        clipped = gpd_seis.clip(polygon)
        a = np.array(clipped.fixedLon)
        b = np.array(clipped.fixedLat)
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

# 📍 Custom legend below map (2-row grid)
from matplotlib.lines import Line2D

legend_elements = [
    Line2D([0], [0], marker='o', color='w', label=list_pulau[i], markerfacecolor=list_color[i], markersize=8)
    for i in range(len(list_pulau))
]

# Arrange legend in 2 rows below the map
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
st.dataframe(stat_df)
