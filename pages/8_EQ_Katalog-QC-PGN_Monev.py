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
st.set_page_config(page_title='Earthquake Dashboard - Katalog QC PGN', layout='wide', page_icon='🌋')

# 📄 Manually specify Excel file path
excel_path = "./fileQC/Data_QC_Gempabumi_Juli_2025.xlsx"  # 🔧 Update this path as needed

try:
    # 📥 Step 1: Load Excel
    df = pd.read_excel(excel_path, header=0)

    # 📍 Step 2: Identify Latitude and Longitude numeric + direction columns
    lat_index = df.columns.get_loc("Latitude")
    lon_index = df.columns.get_loc("Longitude")

    lat_dir_col = df.columns[lat_index + 1]
    lon_dir_col = df.columns[lon_index + 1]

    # 🧮 Step 3: Combine Latitude + Direction
    df["Latitude_Combined"] = df.apply(
        lambda row: f"{row['Latitude']} {str(row[lat_dir_col]).strip().upper()}", axis=1
    )
    df["Longitude_Combined"] = df.apply(
        lambda row: f"{row['Longitude']} {str(row[lon_dir_col]).strip().upper()}", axis=1
    )

    # 🔄 Step 4: Convert to signed float values
    def convert_coord(coord_str):
        try:
            parts = coord_str.split()
            if len(parts) == 2:
                value = float(parts[0])
                direction = parts[1].upper()
                return -abs(value) if direction in ["S", "W"] else abs(value)
        except:
            return np.nan

    df["LAT"] = df["Latitude_Combined"].apply(convert_coord)
    df["LON"] = df["Longitude_Combined"].apply(convert_coord)

    # 📅 Step 5: Parse date column
    if "Date" in df.columns:
        df["DATE"] = pd.to_datetime(df["Date"], errors="coerce")
    else:
        st.warning("⚠️ 'Date' column not found. Using current timestamp instead.")
        df["DATE"] = pd.Timestamp.now()

    # 📊 Step 6: Parse depth and magnitude
    df["DEPTH"] = df["Depth"].astype(str).str.extract(r"(\d+\.?\d*)").astype(float)
    df.rename(columns={"Magnitude": "MAG"}, inplace=True)

    # 📆 Step 7: Date range input
    min_date = df["DATE"].min().date()
    max_date = df["DATE"].max().date()

    st.sidebar.subheader("🕒 Select Date Range")
    start_date, end_date = st.sidebar.date_input(
        "Filter by Date", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )

    # 🧹 Step 8: Filter by date and valid coordinates
    df_filtered = df[
        (df["DATE"].dt.date >= start_date) &
        (df["DATE"].dt.date <= end_date) &
        df["LAT"].between(-90, 90) &
        df["LON"].between(-180, 180)
    ]

    st.subheader("📋 Filtered Earthquake Data")
    st.dataframe(df_filtered[["DATE", "LAT", "LON", "MAG", "DEPTH"]])

except Exception as e:
    st.error(f"❌ Failed to process file: {e}")

# 🧹 Filter Data
#df_filtered = df[
#    df['LAT'].between(df['LAT'].min(), df['LAT'].max()) &
#    df['LON'].between(df['LON'].min(), df['LON'].max())
#]

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
                f"<b>Date:</b> {row['DATE']}<br><b>Mag:</b> {row['MAG']}<br><b>Depth:</b> {row['DEPTH']} km",
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

st.subheader("🗺️ Interactive Seismic Map with Fault Lines")
st_folium(m, width=1000, height=650)

st.subheader("📋 Filtered Earthquake Events")
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
