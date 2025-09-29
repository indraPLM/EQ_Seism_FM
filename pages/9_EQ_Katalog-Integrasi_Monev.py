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
import folium
from streamlit_folium import st_folium
import requests

# 🌍 Page Config
st.set_page_config(page_title='Earthquake Dashboard - Katalog Integrasi', layout='wide', page_icon='🌋')

st.sidebar.subheader("🕒 Select Date Range")
# 📅 Use date_input for better UX
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2025-07-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2025-07-31"))

# 📄 Load Excel file
excel_path = "./pages/fileINTEGRASI/catalog_integrasi_mei-sept_2025.xlsx"
df = pd.read_excel(excel_path)
df.rename(columns={"LAT_FIX": "LAT","LON_FIX": "LON",}, inplace=True)

# 🧹 Filter Data
df_filtered = df[
    df['LAT'].between(df['LAT'].min(), df['LAT'].max()) &
    df['LON'].between(df['LON'].min(), df['LON'].max())
]

# 🔍 Filter by selected date range
df_filtered = df[(df["DATETIME"] >= pd.to_datetime(start_date)) & (df["DATETIME"] <= pd.to_datetime(end_date))]

# 🗺️ Folium Map Construction
def depth_color(depth):
    if depth < 60:
        return 'red'
    elif depth <= 300:
        return 'yellow'
    else:
        return 'green'

if not df_filtered.empty:
    y0 = df_filtered['LAT'].mean()
    x0 = df_filtered['LON'].mean()
else:
    y0, x0 = -2.0, 120.0
    st.warning("⚠️ No data found. Using default map center.")

m = folium.Map(location=(y0, x0), zoom_start=4.5)
folium.TileLayer(
    tiles="https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}",
    attr="ESRI Ocean Basemap",
    name="ESRI Ocean",
    control=False
).add_to(m)

for _, row in df_filtered.iterrows():
    if pd.notnull(row['LAT']) and pd.notnull(row['LON']) and pd.notnull(row['MAG']) and pd.notnull(row['DEPTH']):
        folium.CircleMarker(
            location=[row['LAT'], row['LON']],
            radius=(row['MAG'] ** 1.25),
            color='black',
            weight=0.4,
            fill=True,
            fill_color=depth_color(row['DEPTH']),
            fill_opacity=0.5,
            popup=folium.Popup(
                f"<b>Date:</b> {row['DATETIME']}<br><b>Mag:</b> {row['MAG']}<br><b>Depth:</b> {row['DEPTH']} km",
                max_width=250
            )
        ).add_to(m)

try:
    fault_geojson = requests.get(
        "https://bmkg-content-inatews.storage.googleapis.com/indo_faults_lines.geojson"
    ).json()
    folium.GeoJson(
        fault_geojson,
        name="Fault Lines",
        style_function=lambda feature: {"color": "orange", "weight": 1}
    ).add_to(m)
except Exception as e:
    st.warning(f"⚠️ Fault line overlay failed: {e}")

folium.LayerControl(collapsed=False).add_to(m)

st.subheader(f"🗺️ Seismicities Map Catalog Integration ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")

st_folium(m, width=1000, height=650)

st.subheader(f"📋 Filtered Earthquake Events ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")

df_filtered.index = range(1, len(df_filtered)+1)
st.dataframe(df_filtered)

# 🗺️ Island Setup
list_pulau = ['Sumatra','Jawa','Bali-A','Nustra','Kalimantan','Sulawesi','Maluku','Papua']
list_color = ['r','g','b','y','c','m','purple','orange']
labels     = ['SUMATRA','JAWA','BALI','NUSA TENGGARA','KALIMANTAN','SULAWESI','MALUKU','PAPUA']
projection = ccrs.PlateCarree(central_longitude=120.0)

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

list_pgr = [f'PGR{i}' for i in range(1, 12)]
list_color = plt.cm.get_cmap('tab10', len(list_pgr)).colors

def clip_df(df, pgr_name):
    polygon = gpd.read_file(f"./pages/fileSHP/{pgr_name}.shp")
    geo_df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LON, df.LAT), crs="EPSG:4326")
    return geo_df.clip(polygon)

def get_eq_coords(pgr_name):
    try:
        polygon = gpd.read_file(f"./pages/fileSHP/{pgr_name}.shp")
        clipped = gpd_seis.clip(polygon)
        x, y, _ = projection.transform_points(ccrs.Geodetic(), np.array(clipped.LON), np.array(clipped.LAT)).T
        return x, y
    except Exception as e:
        st.warning(f"Gagal memproses {pgr_name}: {e}")
        return [], []


fig = plt.figure(dpi=300)
ax = fig.add_subplot(111, projection=projection)
ax.set_extent((85, 145, -15, 10))

for i, pgr in enumerate(list_pgr):
    x, y = get_eq_coords(pgr)
    ax.scatter(x, y, s=5, color=list_color[i], marker="o", label=pgr, zorder=3)
    try:
        ax.add_geometries(
            Reader(f"./pages/fileSHP/{pgr}.shp").geometries(),
            ccrs.PlateCarree(),
            facecolor="white",
            edgecolor=list_color[i],
            linewidth=0.5
        )
    except Exception as e:
        st.warning(f"Polygon error on {pgr}: {e}")
        continue

ax.add_feature(cartopy.feature.BORDERS, linestyle='-', linewidth=0.5, alpha=0.5)
ax.coastlines(resolution='10m', color='black', linestyle='-', linewidth=0.5, alpha=0.5)

legend_elements = [
    Line2D([0], [0], marker='o', color='w', label=list_pgr[i], markerfacecolor=list_color[i], markersize=8)
    for i in range(len(list_pgr))
]
ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=4, frameon=False, fontsize='small')

st.markdown("### 🗺️ Seismic Events by PGR Region")
st.pyplot(fig)

stat_rows = [stats(clip_df(df_filtered, reg)) for reg in list_pgr]
stat_df = pd.DataFrame(stat_rows, columns=['<60 km','60–300 km','>300 km','M<4','M4–5','M≥5','Total'])
stat_df['Region'] = list_pgr
stat_df.set_index('Region', inplace=True)

st.subheader("📊 Depth & Magnitude by PGR Region")
stat_df.drop(columns='Total').plot.bar(rot=6, figsize=(15,10))
plt.tight_layout()
plt.savefig("depth_mag_pgr.png")
st.image(Image.open("depth_mag_pgr.png"), caption="Depth & Magnitude per PGR Region")

st.subheader("📋 Earthquake Summary per PGR Region")
st.dataframe(stat_df)
