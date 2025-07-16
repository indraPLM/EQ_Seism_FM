import streamlit as st
import requests
import pandas as pd
import folium
from bs4 import BeautifulSoup
from streamlit_folium import st_folium

# --- Page Setup ---
st.set_page_config(page_title='Kecepatan Prosesing Gempabumi', layout='wide', page_icon="🌍")
st.sidebar.header("Input Parameter:")

# --- Input Parameters ---
time_start = pd.to_datetime(st.sidebar.text_input('Start DateTime:', '2025-03-01 00:00:00'))
time_end   = pd.to_datetime(st.sidebar.text_input('End DateTime:', '2025-03-31 23:59:59'))
North = float(st.sidebar.text_input('North:', '6.0'))
South = float(st.sidebar.text_input('South:', '-13.0'))
West  = float(st.sidebar.text_input('West:', '90.0'))
East  = float(st.sidebar.text_input('East:', '142.0'))

# --- Fetch & Parse QC Focal Data ---

def fetch_qc_focal(url):
    res = requests.get(url)
    raw_text = res.text.strip()
    lines = raw_text.split("\n")
    rows = [line.split("|") for line in lines if "|" in line]
    return rows

qc_data = fetch_qc_focal('http://202.90.198.41/qc_focal.txt')

# --- Extract Columns ---
def get_column(data, col): return [row[col].strip() for row in data[1:-1]]

df = pd.DataFrame({
    'event_id': get_column(qc_data, 0),
    'date_time': pd.to_datetime(get_column(qc_data, 1), errors='coerce'),
    'mag': pd.to_numeric(get_column(qc_data, 5), errors='coerce'),
    'lat': pd.to_numeric([float(x[:-1]) * (-1 if 'S' in x else 1) for x in get_column(qc_data, 7)], errors='coerce'),
    'lon': pd.to_numeric([float(x[:-1]) * (-1 if 'W' in x else 1) for x in get_column(qc_data, 8)], errors='coerce'),
    'depth': pd.to_numeric(get_column(qc_data, 9), errors='coerce')
})

# --- Filter by Magnitude & Region ---
df = df.query('mag >= 5')
df = df[(df['date_time'] > time_start) & (df['date_time'] < time_end)]
df = df[(df['lon'] > West) & (df['lon'] < East) & (df['lat'] > South) & (df['lat'] < North)]

# --- Title Field ---
df['title'] = df.apply(lambda row: f"Tanggal: {row['date_time']}, Mag: {row['mag']}, Depth: {row['depth']}", axis=1)

# --- Fetch Dissemination Time ---
def get_processtime(eventid):
    try:
        url = f"https://bmkg-content-inatews.storage.googleapis.com/history.{eventid.split()[0]}.txt"
        soup = BeautifulSoup(requests.get(url).text, 'html')
        lines = soup.p.text.strip().split('\n')
        parts = lines[1].split('|') if len(lines) > 1 else [' ', ' ']
        return parts[0], float(parts[1])
    except:
        return ' ', None

df[['tstamp_proc', 'time_proc (minutes)']] = pd.DataFrame([get_processtime(eid) for eid in df['event_id']])

# --- Map Visualization ---
tiles = 'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
map_obj = folium.Map(location=[-4, 118], tiles=tiles, attr='ESRI', zoom_start=4.5)

for _, row in df.iterrows():
    folium.Marker([row['lat'], row['lon']], popup=row['title'], icon=folium.Icon(color='red')).add_to(map_obj)

st.markdown("### Peta Seismisitas Gempabumi M ≥5 (BMKG)")
st_folium(map_obj, width=1000)

# --- Chart Visualization ---
st.markdown("### Grafik Kecepatan Prosesing Gempabumi M ≥5")
st.scatter_chart(df, x='date_time', y='time_proc (minutes)')

# --- Table Display ---
st.markdown("### Data Parameter Gempa dan Kecepatan Prosesing")
st.dataframe(df[['event_id', 'date_time', 'tstamp_proc', 'time_proc (minutes)', 'lon', 'lat', 'mag', 'depth']])
