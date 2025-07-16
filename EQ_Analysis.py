import streamlit as st
import pandas as pd
import requests
import geopandas as gpd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from PIL import Image
from streamlit_folium import st_folium
from obspy.geodetics import locations2degrees, degrees2kilometers
import folium

st.set_page_config(page_title="EQ Analysis", layout="wide", page_icon="🌏")

# --- Utility Functions ---
def fetch_text_data(url, delimiter='|'):
    soup = BeautifulSoup(requests.get(url).text, 'html')
    lines = soup.p.text.split('\n') if soup.p else []
    return [line.split(delimiter) for line in lines if delimiter in line]

def extract_xml_tag(soup, tag):
    return [float(x.text) if tag == 'mag' else x.text for x in soup.find_all(tag)]

def to_float(lst): return [float(x) for x in lst]

def match_event(df, t_ref, tol_sec=60):
    matched = df[df['date_time'].apply(lambda t: abs((t_ref - t).total_seconds()) < tol_sec)]
    return matched.iloc[0] if not matched.empty else None

def geo_distance(x0, y0, x1, y1):
    return round(degrees2kilometers(locations2degrees(x0, y0, x1, y1)), 2)

# --- GFZ Data ---
today = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
gfz_raw = fetch_text_data(f'https://geofon.gfz.de/fdsnws/event/1/query?end={today}&limit=40&format=text')
st.write(f'https://geofon.gfz.de/fdsnws/event/1/query?end={today}&limit=40&format=text')

if gfz_raw and len(gfz_raw[0]) > 1:
    gfz_df = pd.DataFrame(gfz_raw[1:], columns=gfz_raw[0])
else:
    st.error("No GFZ data retrieved or parsed. Please check the source or try again later.")
    gfz_df = pd.DataFrame()  # creates empty DataFrame to prevent further downstream crashes

#gfz_df = pd.DataFrame(gfz_raw[1:], columns=gfz_raw[0])
gfz_df['mag'] = to_float(gfz_df[10])
gfz_df['lat'] = to_float(gfz_df[2])
gfz_df['lon'] = to_float(gfz_df[3])
gfz_df['depth'] = to_float(gfz_df[4])
gfz_df['date_time'] = pd.to_datetime(gfz_df[1])
gfz_df['remarks'] = gfz_df[12]

# --- USGS Data ---
usgs = gpd.read_file("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson")
usgs['time_usgs'] = pd.to_datetime(usgs['time'], unit='ms')
usgs['lon'] = usgs.geometry.x
usgs['lat'] = usgs.geometry.y
usgs['depth'] = usgs.geometry.z
usgs['mag'] = usgs['mag']

# --- BMKG Data ---
soup = BeautifulSoup(requests.get("https://bmkg-content-inatews.storage.googleapis.com/live30event.xml").text, 'html')
bmkg_df = pd.DataFrame({
    'eventid': extract_xml_tag(soup, 'eventid'),
    'waktu': extract_xml_tag(soup, 'waktu'),
    'lat': extract_xml_tag(soup, 'lintang'),
    'lon': extract_xml_tag(soup, 'bujur'),
    'mag': to_float(extract_xml_tag(soup, 'mag')),
    'depth': extract_xml_tag(soup, 'dalam'),
    'area': [x.split('\n')[9] for x in extract_xml_tag(soup, 'gempa')]
})
bmkg_df['waktu'] = pd.to_datetime(bmkg_df['waktu'])
bmkg_df = bmkg_df[bmkg_df['mag'] >= 5]

# --- Reference Event ---
x0, y0, m0, d0 = map(float, [bmkg_df['lon'][0], bmkg_df['lat'][0], bmkg_df['mag'][0], bmkg_df['depth'][0]])
t_ref = bmkg_df['waktu'][0]

gfz_match = match_event(gfz_df, t_ref)
usgs_match = match_event(usgs, t_ref)

# --- Map Visualization ---
tiles = "https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}"
m = folium.Map((y0, x0), tiles=tiles, attr="ESRI", zoom_start=8)

folium.GeoJson(
    requests.get("https://bmkg-content-inatews.storage.googleapis.com/indo_faults_lines.geojson").json(),
    style_function=lambda feature: {"color": "orange", "weight": 1}
).add_to(m)

def add_marker(lat, lon, label, color):
    folium.Marker([lat, lon], icon=folium.Icon(icon=label, prefix='fa', color=color)).add_to(m)

add_marker(y0, x0, "1", "red")
if gfz_match is not None:
    add_marker(gfz_match['lat'], gfz_match['lon'], "2", "blue")
if usgs_match is not None:
    add_marker(usgs_match['lat'], usgs_match['lon'], "3", "green")

# --- Metrics Display ---
col1, col2 = st.columns(2)
col1.markdown("## Magnitude")
col2.markdown("## Depth")

cols = st.columns(6)
cols[0].metric("1. BMKG", f"{m0}")
cols[3].metric("1. BMKG", f"{d0}")
if gfz_match is not None:
    delta_mag = round(gfz_match['mag'] - m0, 2)
    delta_depth = round(gfz_match['depth'] - d0, 2)
    dist_km = geo_distance(x0, y0, gfz_match['lon'], gfz_match['lat'])
    cols[1].metric("2. GFZ", f"{gfz_match['mag']}", f"{delta_mag}")
    cols[4].metric("2. GFZ", f"{gfz_match['depth']}", f"{delta_depth}")
else:
    cols[1].metric("2. GFZ", " ")
    cols[4].metric("2. GFZ", " ")
    
if usgs_match is not None:
    delta_mag = round(usgs_match['mag'] - m0, 2)
    delta_depth = round(usgs_match['depth'] - d0, 2)
    dist_km = geo_distance(x0, y0, usgs_match['lon'], usgs_match['lat'])
    cols[2].metric("3. USGS", f"{usgs_match['mag']}", f"{delta_mag}")
    cols[5].metric("3. USGS", f"{usgs_match['depth']}", f"{delta_depth}")
else:
    cols[2].metric("3. USGS", " ")
    cols[5].metric("3. USGS", " ")

# --- Location Display ---
st.markdown("## Longitude/Latitude")
loc_cols = st.columns(3)
loc_cols[0].metric("1. BMKG", f"{x0} ; {y0}")
if gfz_match is not None:
    dist_km = geo_distance(x0, y0, gfz_match['lon'], gfz_match['lat'])
    loc_cols[1].metric("2. GFZ", f"{gfz_match['lon']} ; {gfz_match['lat']}", f"{dist_km} Km")
else:
    loc_cols[1].metric("2. GFZ", " ")

if usgs_match is not None:
    dist_km = geo_distance(x0, y0, usgs_match['lon'], usgs_match['lat'])
    loc_cols[2].metric("3. USGS", f"{usgs_match['lon']} ; {usgs_match['lat']}", f"{dist_km} Km")
else:
    loc_cols[2].metric("3. USGS", " ")

# --- Final Outputs ---
st_data = st_folium(m, width=1000)
st.markdown("### 15 Data Gempabumi Terkini")
st.table(bmkg_df)

st.markdown("""### Link Website
- [BMKG](https://www.bmkg.go.id/)
- [InaTEWS](https://inatews.bmkg.go.id/)
- [WebDC BMKG](https://geof.bmkg.go.id/webdc3/)
""")
