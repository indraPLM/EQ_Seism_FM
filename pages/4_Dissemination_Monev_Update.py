import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title='TSP Monitoring dan Evaluasi', layout='wide', page_icon="🌍")
st.sidebar.header("Input Parameter :")

time_start = st.sidebar.text_input('Start DateTime:', '2025-03-01 00:00:00')
time_end   = st.sidebar.text_input('End DateTime:', '2025-03-31 23:59:59')

# --- Helpers ---
def extract_text(tag): return [t.text.strip() for t in soup.find_all(tag)]
def strip_timezone(t): return t.replace('WIB', '').replace('UTC', '').strip()
def convert_lat(lat): return -float(lat.replace('LS', '').strip()) if 'LS' in lat else float(lat.replace('LU', '').strip())
def convert_lon(lon): return -float(lon.replace('BB', '').strip()) if 'BB' in lon else float(lon.replace('BT', '').strip())

# --- Data Fetch ---
url = 'https://bmkg-content-inatews.storage.googleapis.com/last30event.xml'
soup = BeautifulSoup(requests.get(url).text, 'html')

# --- Raw Extraction ---
dates      = extract_text('date')
times      = list(map(strip_timezone, extract_text('time')))
timesent   = list(map(strip_timezone, extract_text('timesent')))
latitudes  = list(map(convert_lat, extract_text('latitude')))
longitudes = list(map(convert_lon, extract_text('longitude')))
magnitudes = extract_text('magnitude')
depths     = extract_text('depth')
statuses   = extract_text('potential')

# --- DataFrame Construction ---
df = pd.DataFrame({
    'datetime': pd.to_datetime(pd.Series(dates) + ' ' + pd.Series(times)),
    'timesent': pd.to_datetime(timesent),
    'lat': latitudes,
    'lon': longitudes,
    'mag': magnitudes,
    'depth': depths,
    'status': statuses
})
df['lapsetime (minutes)'] = ((df['timesent'] - df['datetime']).dt.total_seconds() / 60).round(2)
df['title'] = [f'Tanggal: {d} {t}, Mag: {m}, Depth: {dp}' for d, t, m, dp in zip(dates, times, magnitudes, depths)]

# --- Folium Map ---
tiles = 'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
m = folium.Map(location=[-4, 118], tiles=tiles, attr='ESRI', zoom_start=4.5)

for lat, lon, title in zip(df['lat'], df['lon'], df['title']):
    folium.Marker([lat, lon], popup=title, icon=folium.Icon(color='red')).add_to(m)

st.markdown("### Seismisitas 30 Kejadian Gempabumi terakhir (BMKG)")
st_folium(m, width=1000)

# --- Filtered Scatter Chart ---
start_dt = pd.to_datetime(time_start)
end_dt   = pd.to_datetime(time_end)

df_filtered = df[(df['datetime'] > start_dt) & (df['datetime'] < end_dt)]
#df_filtered = df[(df['datetime'] > time_start) & (df['datetime'] < time_end)]
st.markdown("### Grafik Kecepatan Diseminasi Gempabumi M >=5")
st.scatter_chart(df_filtered, x='datetime', y='lapsetime (minutes)')

st.markdown("### Data Parameter Gempa dan Perbedaan Waktu Pengiriman Informasi")
st.dataframe(df)
