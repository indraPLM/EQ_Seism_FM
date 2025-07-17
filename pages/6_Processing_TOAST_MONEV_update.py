import streamlit as st
import pandas as pd
import requests
import os
from bs4 import BeautifulSoup

# --- Page Setup ---
st.set_page_config(page_title='Kecepatan Processing Tsunami TOAST', layout='wide', page_icon="🌍")
st.sidebar.header("Input Parameter:")

# --- Input Parameters ---
time_start = pd.to_datetime(st.sidebar.text_input('Start DateTime:', '2025-03-01 00:00:00'))
time_end   = pd.to_datetime(st.sidebar.text_input('End DateTime:', '2025-03-31 23:59:59'))
North      = float(st.sidebar.text_input('North:', '6.0'))
South      = float(st.sidebar.text_input('South:', '-13.0'))
West       = float(st.sidebar.text_input('West:', '90.0'))
East       = float(st.sidebar.text_input('East:', '142.0'))

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
st.dataframe(df_toast)

toast_files = os.listdir("./pages/filetoast/")
st.write("📁 Detected TOAST files:", toast_files)

def load_toast_logs(path="./pages/filetoast/"):
    for fname in os.listdir(path):
        eid = fname.split('.log')[0]
        with open(os.path.join(path, fname)) as f:
            lines = f.readlines()
        st.write(f"🔍 File: {fname}", lines)
        break  # Just show one file for now

path="./pages/filetoast/"
dir_list = os.listdir(path)

event_list = []
for i in range(len(dir_list)):
    temp=dir_list[i].split('.log')
    temp=temp[0]
    event_list.append(temp)

text_toast=[]
for i in range(len(dir_list)):
    curr=os.getcwd() 
    test=dir_list[i]
    with open(path+'/'+test) as f:
        lines = f.readlines()
        text_toast.append(lines)
print([len(text_toast),len(event_list)])

dttime_toast, remark_toast, eventid_toast = [], [], []

for i in range(len(text_toast)):
    if event_list[i].startswith('bmg202'):
        for line in text_toast[i]:
            parts = line.strip().split()
            # Look for lines that begin with a valid timestamp
            if len(parts) >= 3:
                try:
                    pd.to_datetime(parts[0] + ' ' + parts[1])  # Validate timestamp
                    dttime = parts[0] + ' ' + parts[1]
                    remark = parts[2]
                    dttime_toast.append(dttime)
                    remark_toast.append(remark)
                    eventid_toast.append(event_list[i])
                    break  # Take the first valid timestamped line only
                except:
                    continue

df_toast1 = pd.DataFrame({'event_id': eventid_toast,
                         'tstamp_toast': dttime_toast,
                         'remark_toast': remark_toast})
df_toast1['tstamp_toast'] = pd.to_datetime(df_toast1['tstamp_toast'], errors='coerce')
st.dataframe(df_toast1)

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
df = df[df['event_id'].str.strip().str.startswith('bmg')].copy()
st.dataframe(df)
st.dataframe(df_toast)

# --- Merge with TOAST data ---
df_merge = pd.merge(df, df_toast, on='event_id')
df_merge['lapse_time_toast'] = (df_merge['tstamp_toast'] - df_merge['date_time_wib']).dt.total_seconds() / 60
df_merge = df_merge.query('lapse_time_toast <= 60')

# --- Visualization: Map ---
st.markdown("### Peta Lokasi Gempabumi Prosesing TOAST M ≥5")
st.map(df_merge, latitude='lat', longitude='lon', size=2000, zoom=3)

# --- Visualization: Chart ---
st.markdown("### Grafik Kecepatan Prosesing TOAST M ≥5")
st.scatter_chart(df_merge, x='date_time_wib', y='lapse_time_toast')

# --- Table Display ---
st.markdown("### Data Parameter Gempa dan Kecepatan Prosesing TOAST")
st.dataframe(df_merge[['event_id','date_time','tstamp_toast','lapse_time_toast','lon','lat','mag','depth']])
