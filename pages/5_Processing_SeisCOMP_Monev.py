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
time_start = pd.to_datetime(st.sidebar.text_input('Start DateTime:', '2025-06-01 00:00:00'))
time_end   = pd.to_datetime(st.sidebar.text_input('End DateTime:', '2025-06-30 23:59:59'))
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
df = df[(df['date_time'] > time_start) & (df['date_time'] < time_end)]
df = df[(df['fixedLon'] > West) & (df['fixedLon'] < East) & (df['fixedLat'] > South) & (df['fixedLat'] < North)]

# --- Title Field ---
df['title'] = df.apply(lambda row: f"Tanggal: {row['date_time']}, Mag: {row['mag']}, Depth: {row['depth']}", axis=1)

df = df[df['event_id'].str.strip().str.startswith('bmg')].copy()
# --- Fetch Dissemination Time ---
# --- Revised Dissemination Time Fetch ---
def load_seiscomp_process(url):
    res = requests.get(url)
    raw_text = res.text.strip()
    lines = raw_text.split("\n")
    rows = [line.split("|") for line in lines if "|" in line]
    return rows
    
def manual_fetch_timestamp(eventid):
    try:
        eid = eventid.strip()
        url = f"https://bmkg-content-inatews.storage.googleapis.com/history.{eid}.txt"
        rows = load_seiscomp_process(url)

        if not rows or len(rows[0]) < 2:
            return 0.0, 0.0

        ts_raw = rows[0][0].strip()
        elapse_raw = rows[0][1].strip()

        t_stamp = pd.to_datetime(ts_raw, errors='coerce')
        elapse = float(elapse_raw) if elapse_raw else 0.0
        ts_float = t_stamp.timestamp() if pd.notnull(t_stamp) else 0.0

        return ts_float, elapse
    except:
        return 0.0, 0.0
# 🧹 Strip trailing space from event_id before applying function
df['event_id'] = df['event_id'].str.strip()

# Extract timestamp and processing time
results = [manual_fetch_timestamp(eid) for eid in df['event_id']]
results_df = pd.DataFrame(results, columns=['tstamp_process', 'time_process (minutes)'])

# Combine with original DataFrame
df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
df['tstamp_process'] = pd.to_datetime(df['tstamp_process'], unit='s', errors='coerce')

df['date'] = df['date_time'].dt.strftime('%d-%b-%y')       # Example: 04-Jun-25
df['OT'] = df['date_time'].dt.strftime('%H:%M:%S')          # Example: 06:38:40
df['Proc Time'] = df['tstamp_process'].dt.strftime('%H:%M:%S')   # Example: 06:41:41

def minutes_to_hms(minutes):
    if pd.isnull(minutes): return ''
    total_seconds = int(minutes * 60)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

df['lapsetime (HH:MM:SS)'] = df['time_process (minutes)'].apply(minutes_to_hms)

# --- Map Visualization ---
tiles = 'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
map_obj = folium.Map(location=[-4, 118], tiles=tiles, attr='ESRI', zoom_start=4.5)

for _, row in df.iterrows():
    folium.Marker([row['fixedLat'], row['fixedLon']], popup=row['title'], icon=folium.Icon(color='red')).add_to(map_obj)

st.markdown("### Peta Seismisitas Gempabumi M ≥5 (BMKG)")
st_folium(map_obj, width=1000)

# --- Chart Visualization ---
st.markdown("### Grafik Kecepatan Prosesing SeisCOMP Gempabumi M ≥5")
#st.scatter_chart(df_display, x='date_time', y='elapse(minutes)')

import altair as alt

# Filter clean data
df_plot = df[df['time_process (minutes)'] > 0]

# Define base chart
chart = alt.Chart(df_plot).mark_point(filled=False, size=80).encode(
    x='date_time:T',
    y=alt.Y('time_process (minutes):Q', scale=alt.Scale(domain=[0, 5])),
    shape=alt.condition(
        alt.datum['time_process (minutes)'] > 3, alt.ShapeValue('cross'), alt.ShapeValue('circle')
    ),
    color=alt.condition(
        alt.datum['time_process (minutes)'] > 3, alt.value('red'), alt.value('steelblue')
    ),
    tooltip=['event_id', 'date_time', 'mag', 'depth']
).properties(
    width=900,
    height=400,
    title=alt.TitleParams(
        text='Grafik Kecepatan Prosesing SeisCOMP Gempabumi M ≥5 ',
        anchor='middle',  # ✅ This centers the title
        fontSize=18
    )
)

st.altair_chart(chart, use_container_width=True)

# --- Table Display ---
st.markdown("### KECEPATAN ANALISIS PROCESSING INFORMASI GEMPABUMI")
st.markdown(f"### 🕒 Periode Monitoring: `{time_start}` s.d. `{time_end}`")

df.rename(columns={
    'date':'Date',
    'OT':'OT (UTC) Gempa',
    'Proc Time':'OT-Create (UTC)',
    'fixedLat': 'Lat-Diss',
    'fixedLon': 'Lon-Diss',
    'lapsetime (HH:MM:SS)':'Selisih OT dengan Create FL',
    'mag': 'Mag Diss',
    'depth': 'Depth-Diss (Km)',
    'remarks': 'Lokasi'
}, inplace=True)
df_show=df[['Date','OT (UTC) Gempa', 'OT-Create (UTC)','Selisih OT dengan Create FL',
            'Mag Diss','Lat-Diss','Lon-Diss','Depth-Diss (Km)','Lokasi']]
df_show.index = range(1, len(df_show) + 1)
st.dataframe(df_show)

#df.index = range(1, len(df_display) + 1)
st.dataframe(df)
