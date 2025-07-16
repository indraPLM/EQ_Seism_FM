import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime

# --- Page Setup ---
st.set_page_config(page_title='TSP Monitoring dan Evaluasi', layout='wide', page_icon="🌍")
st.sidebar.header("Input Parameter :")

# Calculate dynamic dates
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
month_before = yesterday - datetime.timedelta(days=30)

# Format as strings
yesterday_str = yesterday.strftime('%Y-%m-%d %H:%M:%S')
month_before_str = month_before.strftime('%Y-%m-%d %H:%M:%S')

# Sidebar inputs with default values
time_start = st.sidebar.text_input('Start DateTime:', month_before_str)
time_end = st.sidebar.text_input('End DateTime:', yesterday_str)

#time_start = st.sidebar.text_input('Start DateTime:', '2025-03-01 00:00:00')
#time_end   = st.sidebar.text_input('End DateTime:', '2025-03-31 23:59:59')

# --- Helper Functions ---
def extract_text(tag): return [t.text.strip() for t in soup.find_all(tag)]

def parse_date_time(date_str, time_str):
    combo = f"{date_str.strip()} {time_str.strip().replace('WIB','').replace('UTC','')}"
    for fmt in ["%d-%m-%y %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d-%b-%y %H:%M:%S"]:
        try:
            return pd.to_datetime(combo, format=fmt)
        except ValueError:
            continue
    return pd.NaT


def parse_timesent(ts):
    ts = ts.strip().replace('WIB','').replace('UTC','')
    for fmt in ["%d/%m/%Y %H:%M:%S", "%d-%b-%y %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
        try: return pd.to_datetime(ts, format=fmt)
        except: continue
    return pd.NaT

def convert_lat(lat): return -float(lat.replace('LS','').strip()) if 'LS' in lat else float(lat.replace('LU','').strip())
def convert_lon(lon): return -float(lon.replace('BB','').strip()) if 'BB' in lon else float(lon.replace('BT','').strip())

# --- Fetch and Parse XML ---
url = 'https://bmkg-content-inatews.storage.googleapis.com/last30event.xml'
soup = BeautifulSoup(requests.get(url).text, 'html')

timesent  = extract_text('timesent')
lats      = extract_text('latitude')
lons      = extract_text('longitude')
mags      = extract_text('magnitude')
depths    = extract_text('depth')
areas  = extract_text('area')

# --- Build DataFrame with Validated Parsing ---
df = pd.DataFrame({
    'timesent': [parse_timesent(ts) for ts in timesent],
    'lat': list(map(convert_lat, lats)),
    'lon': list(map(convert_lon, lons)),
    'mag': mags,
    'depth': depths
})

dates     = extract_text('date')
times     = extract_text('time')

def format_date_str(d):
    parts = d.strip().split('-')  # e.g. "14-07-25"
    if len(parts) == 3:
        day, month, year = parts
        year = '20' + year if len(year) == 2 else year  # Safeguard against YY
        return f"{day}/{month}/{year}"
    return d  # fallback

# Clean time: remove "WIB" or "UTC" and strip
clean_time = [t.replace('WIB', '').replace('UTC', '').strip() for t in times]
clean_date = [format_date_str(d) for d in dates]

# Combine and convert to datetime
combined_dt = [f"{d} {t}" for d, t in zip(clean_date, clean_time)]

df['datetime'] = pd.to_datetime(combined_dt, format="%d/%m/%Y %H:%M:%S", errors='coerce')

df['lapsetime (minutes)'] = df['timesent']-df['datetime']
df['lapsetime (minutes)'] = (df['lapsetime (minutes)'].dt.total_seconds()/60).round(2)
df['title'] = [f'Tanggal: {d} {t}, Mag: {m}, Depth: {dp}' for d, t, m, dp in zip(dates, times, mags, depths)]

# --- Interactive Map ---
tiles = 'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
map_obj = folium.Map(location=[-4, 118], tiles=tiles, attr='ESRI', zoom_start=4.5)
for lat, lon, title in zip(df['lat'], df['lon'], df['title']):
    folium.Marker([lat, lon], popup=title, icon=folium.Icon(color='red')).add_to(map_obj)

st.markdown("### Seismisitas 30 Kejadian Gempabumi terakhir (BMKG)")
st_folium(map_obj, width=1000)

# --- Date Filtering ---
try:
    start_dt = pd.to_datetime(time_start, errors='coerce')
    end_dt   = pd.to_datetime(time_end, errors='coerce')
    filtered = df[(df['datetime'] > start_dt) & (df['datetime'] < end_dt)]
except:
    st.warning("🧭 Format waktu tidak valid. Pastikan input sesuai contoh: YYYY-MM-DD HH:MM:SS")
    filtered = pd.DataFrame()

# --- Chart & Table Display ---
st.markdown("### Grafik Kecepatan Diseminasi Gempabumi M >=5")
if not filtered.empty:
    st.scatter_chart(filtered, x='datetime', y='lapsetime (minutes)')
else:
    st.info("📉 Tidak ada data dalam rentang waktu yang dipilih.")

import altair as alt

# Add a flag column for threshold
threshold = 3.0
df_filtered = filtered.copy()
df_filtered['flag'] = df_filtered['lapsetime (minutes)'].astype(float) > threshold

# Create the base chart
base = alt.Chart(df_filtered).encode(
    x='datetime:T',
    y='lapsetime (minutes):Q'
)

# Circle markers below threshold
circles = base.transform_filter('datum.flag == false').mark_circle(size=60, color='blue')

# X markers above threshold
crosses = base.transform_filter('datum.flag == true').mark_point(
    shape='cross', color='red', size=80, strokeWidth=2
)

# Threshold line
rule = alt.Chart(pd.DataFrame({'y': [threshold]})).mark_rule(
    color='gray', strokeDash=[6, 3]
).encode(y='y:Q')

# Compose and display
st.altair_chart(circles + crosses + rule, use_container_width=True)

response = requests.get(url)
# Use XML-aware parser for correct tag detection
soup = BeautifulSoup(response.text, 'xml')  # <- critical change here

# Extract area safely
areas = soup.find_all('area')
if not areas:
    st.warning("🚨 Tag <area> not found — check XML structure or parser type.")
else:
    list_areas = [a.text.strip() for a in areas]
    df['area'] = list_areas  # assuming alignment with other fields

st.markdown("### Data Parameter Gempa dan Perbedaan Waktu Pengiriman Informasi")

required_cols = ['datetime', 'timesent', 'lon', 'lat', 'mag', 'depth', 'area']
existing_cols = [col for col in required_cols if col in df.columns]
df_show = df[existing_cols]
df_show.index = range(1, len(df_show) + 1)  # Reindex starting from 1
st.dataframe(df_show)

