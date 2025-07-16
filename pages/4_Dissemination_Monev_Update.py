import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

# --- Page Setup ---
st.set_page_config(page_title='TSP Monitoring dan Evaluasi', layout='wide', page_icon="🌍")
st.sidebar.header("Input Parameter :")
time_start = st.sidebar.text_input('Start DateTime:', '2025-03-01 00:00:00')
time_end   = st.sidebar.text_input('End DateTime:', '2025-03-31 23:59:59')

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
statuses  = extract_text('potential')

# --- Build DataFrame with Validated Parsing ---
df = pd.DataFrame({
    'timesent': [parse_timesent(ts) for ts in timesent],
    'lat': list(map(convert_lat, lats)),
    'lon': list(map(convert_lon, lons)),
    'mag': mags,
    'depth': depths,
    'status': statuses
})

dates     = extract_text('date')
times     = extract_text('time')
# --- Manual DateTime Assembly ---
clean_time = [t.replace('WIB', '').replace('UTC', '').strip() for t in times]
clean_date = [d.strip() for d in dates]
combined_dt = [f"{d} {t}" for d, t in zip(clean_date, clean_time)]

# Convert to datetime with coercion
df['datetime'] = pd.to_datetime(combined_dt, errors='coerce')

df['lapsetime (minutes)'] = ((df['timesent'] - df['datetime']).dt.total_seconds() / 60).round(2)
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

st.markdown("### Data Parameter Gempa dan Perbedaan Waktu Pengiriman Informasi")
st.dataframe(df)
