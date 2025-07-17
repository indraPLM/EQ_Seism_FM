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
        eid = fname.split('.log')[0]
        if not eid.startswith('bmg202'):
            continue
        with open(os.path.join(path, fname)) as f:
            lines = f.readlines()
            if len(lines) >= 3:
                parts = lines[2].split()
                dt = parts[0] + ' ' + parts[1]
                event_ids.append(eid)
                timestamps.append(dt)
                remarks.append(parts[2])
    df_toast = pd.DataFrame({'event_id': event_ids, 'tstamp_toast': timestamps, 'remark_toast': remarks})
    df_toast['tstamp_toast'] = pd.to_datetime(df_toast['tstamp_toast'])
    return df_toast

df_toast = load_toast_logs()

# --- Parse QC Catalog ---
def fetch_qc(url='http://202.90.198.41/qc.txt'):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    if not soup.p or not soup.p.text:
        return pd.DataFrame()
    rows = [line.split('|') for line in soup.p.text.strip().split('\n') if line]
    rows = rows[1:-2]  # Remove header and footer
    columns = ['event_id','date_time','mode','status','phase','mag','type_mag',
               'n_mag','azimuth','rms','lat','lon','depth','type_event','remarks']
    return pd.DataFrame([dict(zip(columns, r)) for r in rows])

df_qc = fetch_qc()
if df_qc.empty:
    st.error("⚠️ Gagal mengambil data QC.")
    st.stop()

# --- Clean QC Data ---
def fix_coords(df):
    df['event_id'] = df['event_id'].str.strip()
    df['lat'] = df['lat'].str.extract(r'([\d.]+)')[0].astype(float) * df['lat'].str.contains('S').apply(lambda x: -1 if x else 1)
    df['lon'] = df['lon'].str.extract(r'([\d.]+)')[0].astype(float) * df['lon'].str.contains('W').apply(lambda x: -1 if x else 1)
    df['depth'] = df['depth'].str.replace('km','', regex=False).astype(float)
    df['mag'] = pd.to_numeric(df['mag'], errors='coerce')
    df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')
    df['date_time_wib'] = df['date_time'] + pd.Timedelta(hours=7)
    return df

df_qc = fix_coords(df_qc)
df_qc = df_qc.query('mag >= 5')
df_qc = df_qc[(df_qc['date_time'] > time_start) & (df_qc['date_time'] < time_end)]
df_qc = df_qc[(df_qc['lat'] > South) & (df_qc['lat'] < North) & (df_qc['lon'] > West) & (df_qc['lon'] < East)]

# --- Merge with TOAST data ---
df_merge = pd.merge(df_qc, df_toast, on='event_id')
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
