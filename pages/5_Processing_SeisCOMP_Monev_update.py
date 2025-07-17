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

# --- Filter by Magnitude & Region ---
df = df.query('mag >= 5')
#st.dataframe(df)
df = df[(df['date_time'] > time_start) & (df['date_time'] < time_end)]
df = df[(df['fixedLon'] > West) & (df['fixedLon'] < East) & (df['fixedLat'] > South) & (df['fixedLat'] < North)]

# --- Title Field ---
df['title'] = df.apply(lambda row: f"Tanggal: {row['date_time']}, Mag: {row['mag']}, Depth: {row['depth']}", axis=1)
#st.dataframe(df)

# --- Fetch Dissemination Time ---
def manual_fetch_timestamp(eventid):
    try:
        eid = eventid.strip()
        url = f"https://bmkg-content-inatews.storage.googleapis.com/history.{eid}.txt"
        response = requests.get(url)

        text = response.text.strip()
        lines = text.split('\n')

        # Skip header line — get first data line
        if len(lines) < 2:
            return None, None

        row2 = lines[1].split('|')
        if len(row2) >= 2:
            t_stamp = pd.to_datetime(row2[0].strip(), errors='coerce')
            elapse = float(row2[1].strip())
            return t_stamp, elapse

        return None, None
    except Exception:
        return None, None

        
# Assign fetched values to DataFrame
df[['tstamp_proc', 'time_proc (minutes)']] = pd.DataFrame([
    manual_fetch_timestamp(eid) for eid in df['event_id']
])

def load_seiscomp_process(url):
    res = requests.get(url)
    raw_text = res.text.strip()
    lines = raw_text.split("\n")
    rows = [line.split("|") for line in lines if "|" in line]
    return rows


test_id = df['event_id'].iloc[0]
test_url = f"https://bmkg-content-inatews.storage.googleapis.com/history.{test_id}.txt"
text_url =load_seiscomp_process(test_url)
st.text(test_url)
st.text(text_url)  # Show exact raw file contents

#df[['tstamp_proc', 'time_proc (minutes)']] = pd.DataFrame([get_processtime(eid) for eid in df['event_id']])

# --- Map Visualization ---
tiles = 'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
map_obj = folium.Map(location=[-4, 118], tiles=tiles, attr='ESRI', zoom_start=4.5)

for _, row in df.iterrows():
    folium.Marker([row['fixedLat'], row['fixedLon']], popup=row['title'], icon=folium.Icon(color='red')).add_to(map_obj)

st.markdown("### Peta Seismisitas Gempabumi M ≥5 (BMKG)")
st_folium(map_obj, width=1000)

# --- Chart Visualization ---
st.markdown("### Grafik Kecepatan Prosesing Gempabumi M ≥5")
st.scatter_chart(df, x='date_time', y='time_proc (minutes)')

# --- Table Display ---
st.markdown("### Data Parameter Gempa dan Kecepatan Prosesing")
st.dataframe(df[['event_id', 'date_time', 'tstamp_proc', 'time_proc (minutes)', 'lon', 'lat', 'mag', 'depth']])
