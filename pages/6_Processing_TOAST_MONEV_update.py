import streamlit as st
import pandas as pd
import requests
import os
from bs4 import BeautifulSoup

# --- Page Setup ---
st.set_page_config(page_title='Kecepatan Processing Tsunami TOAST', layout='wide', page_icon="🌍")

with st.sidebar:
    st.header("Input Parameter:")

    time_start = pd.to_datetime(st.text_input('Start DateTime:', '2025-03-01 00:00:00'))
    time_end   = pd.to_datetime(st.text_input('End DateTime:', '2025-03-31 23:59:59'))
    North      = float(st.text_input('North:', '6.0'))
    South      = float(st.text_input('South:', '-13.0'))
    West       = float(st.text_input('West:', '90.0'))
    East       = float(st.text_input('East:', '142.0'))

# --- Parse TOAST Logs ---
def load_toast_logs(path="./pages/filetoast/"):
    event_ids, timestamps, remarks = [], [], []
    for fname in os.listdir(path):
        if not fname.endswith('.log'):
            continue
        eid = fname.split('.log')[0]
        with open(os.path.join(path, fname)) as f:
            lines = f.readlines()

        # 🔍 Look for the first line that includes "Incident created" or similar marker
        for line in lines:
            if "Incident created" in line or "Info" in line:
                parts = line.strip().split()
                if len(parts) >= 3:
                    ts = parts[0] + ' ' + parts[1]
                    remark = parts[2]
                    event_ids.append(eid)
                    timestamps.append(ts)
                    remarks.append(remark)
                break  # Use only the first matching line
    df_toast = pd.DataFrame({'event_id': event_ids, 'tstamp_toast': timestamps, 'remark_toast': remarks})
    df_toast['tstamp_toast'] = pd.to_datetime(df_toast['tstamp_toast'], errors='coerce')
    return df_toast

df_toast = load_toast_logs()
df_toast['tstamp_toast'] = df_toast['tstamp_toast'] - pd.Timedelta(hours=7)

# 🔎 Load Earthquake Catalog (with robust HTML fallback)
#@st.cache_data(show_spinner=False)
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
    df['mag'] = df['mag'].astype(float).round(2)
    df['sizemag'] = df['mag'] * 1000
    df['date_time'] = pd.to_datetime(df['date_time'])

    return df

df = preprocess(df)

# --- Filter by Magnitude & Region ---
df = df.query('mag >= 5')
df = df[(df['date_time'] > time_start) & (df['date_time'] < time_end)]
df = df[(df['fixedLon'] > West) & (df['fixedLon'] < East) & (df['fixedLat'] > South) & (df['fixedLat'] < North)]
df = df[df['event_id'].str.strip().str.startswith('bmg')].copy()

# Strip whitespace, ensure consistent casing and type
df['event_id'] = df['event_id'].astype(str).str.strip()
df_toast['event_id'] = df_toast['event_id'].astype(str).str.strip()
df['mag'] = pd.to_numeric(df['mag'], errors='coerce').round(2)

# --- Merge with TOAST data ---
df_merge = pd.merge(df, df_toast, on='event_id')
df_merge['lapse_time_toast'] = (df_merge['tstamp_toast'] - df_merge['date_time']).dt.total_seconds() / 60
df_merge = df_merge.query('lapse_time_toast <= 60')

# --- Visualization: Map ---
import folium
from streamlit_folium import st_folium

# --- Custom Ocean Basemap ---
tiles = 'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
map_obj = folium.Map(location=[-3, 115], tiles=tiles, attr='ESRI', zoom_start=4.5)

# --- Add Event Markers ---
for _, row in df_merge.iterrows():
    popup_text = (
        f"<b>Event ID:</b> {row['event_id']}<br>"
        f"<b>DateTime:</b> {row['date_time'].strftime('%Y-%m-%d %H:%M:%S')}<br>"
        f"<b>Mag:</b> {row['mag']:.2f}<br>"
        f"<b>Delay:</b> {row['lapse_time_toast']:.2f} min"
    )
    folium.CircleMarker(
        location=[row['fixedLat'], row['fixedLon']],
        radius=row['mag'] * 2,  # scale marker size by magnitude
        color="crimson" if row['lapse_time_toast'] > 3 else "green",
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=row['event_id']
    ).add_to(map_obj)

# --- Display Folium Map in Streamlit ---
st.markdown("### 🌐 Peta Lokasi Gempabumi dengan TOAST M ≥5")
st_folium(map_obj, width=900, height=500)


# --- Visualization: Chart ---
st.markdown("### Grafik Kecepatan Prosesing TOAST M ≥5")
df_merge['mag_str'] = df_merge['mag'].map("{:.2f}".format)

import altair as alt

chart = alt.Chart(df_merge).mark_point(size=70, filled=True).encode(
    x='date_time:T',
    y='lapse_time_toast:Q',
    tooltip=['event_id','date_time','tstamp_toast','lapse_time_toast','lon','lat','mag','depth']
).properties(
    width=800,
    height=400,
    title="Grafik Kecepatan Prosesing TOAST M ≥5"
)

st.altair_chart(chart, use_container_width=True)

# --- Table Display ---
st.markdown("### Data Parameter Gempa dan Kecepatan Prosesing TOAST")

st.dataframe(df_merge[['event_id','date_time','tstamp_toast','lapse_time_toast','lon','lat','mag_str','depth','remarks']])
