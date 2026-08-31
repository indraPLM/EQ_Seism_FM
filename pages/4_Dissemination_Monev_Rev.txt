import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime
import altair as alt
from calendar import monthrange

# --- Page Setup ---
st.set_page_config(page_title='TSP Monitoring dan Evaluasi', layout='wide', page_icon="🌍")
st.sidebar.header("Input Parameter :")

tim_tod = datetime.datetime.today()
tim_yea = tim_tod.year - (1 if tim_tod.month == 1 else 0)
tim_mon = (12 if tim_tod.month == 1 else tim_tod.month - 1)
tim_end_def = datetime.datetime(
    year=tim_yea,
    month=tim_mon,
    day=monthrange(tim_yea, tim_mon)[1],
    hour=23,
    minute=59,
    second=59
)
tim_sta_def = datetime.datetime(
    year=tim_yea,
    month=tim_mon,
    day=1,
    hour=0,
    minute=0,
    second=0
)
time_sta = st.sidebar.datetime_input("Start DateTime", tim_sta_def)
time_end = st.sidebar.datetime_input("End DateTime", tim_end_def)

# --- Helper Functions ---
def extract_text(tag, soup_obj): 
    return [t.text.strip() for t in soup_obj.find_all(tag)]

def parse_timesent(ts):
    ts = ts.strip().replace('WIB', '').replace('UTC', '')
    for fmt in ["%d/%m/%Y %H:%M:%S", "%d-%b-%y %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
        try: 
            return pd.to_datetime(ts, format=fmt)
        except Exception: 
            continue
    return pd.NaT

def convert_lat(lat): 
    return -float(lat.replace('LS', '').strip()) if 'LS' in lat else float(lat.replace('LU', '').strip())

def convert_lon(lon): 
    return -float(lon.replace('BB', '').strip()) if 'BB' in lon else float(lon.replace('BT', '').strip())

def format_date_str(d):
    parts = d.strip().split('-')  # e.g. "29-08-26" or "29-08-2026"
    if len(parts) == 3:
        day, month, year = parts
        year = '20' + year if len(year) == 2 else year
        return f"{day}/{month}/{year}"
    return d

def minutes_to_hms(minutes):
    if pd.isnull(minutes): 
        return ''
    total_seconds = int(minutes * 60)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# --- Fetch and Parse XML (XML Parser) ---
url = 'https://bmkg-content-inatews.storage.googleapis.com/last30event.xml'
response = requests.get(url, timeout=10)

# Use 'xml' parser from the very beginning
soup = BeautifulSoup(response.text, 'xml')

timesent = extract_text('timesent', soup)
lats     = extract_text('latitude', soup)
lons     = extract_text('longitude', soup)
mags     = extract_text('magnitude', soup)
depths   = extract_text('depth', soup)
areas    = extract_text('area', soup)
dates    = extract_text('date', soup)
times    = extract_text('time', soup)

# Clean date and time fields
clean_time = [t.replace('WIB', '').replace('UTC', '').strip() for t in times]
clean_date = [format_date_str(d) for d in dates]
combined_dt = [f"{d} {t}" for d, t in zip(clean_date, clean_time)]

# --- Build DataFrame ---
df = pd.DataFrame({
    'timesent': [parse_timesent(ts) for ts in timesent],
    'lat': [convert_lat(l) for l in lats],
    'lon': [convert_lon(l) for l in lons],
    'Lat-Diss': lats,
    'Lon-Diss': lons,
    'mag': mags,
    'depth': depths,
    'area': areas,
    'datetime': pd.to_datetime(combined_dt, format="%d/%m/%Y %H:%M:%S", errors='coerce')
})

df['lapsetime (minutes)'] = df['timesent'] - df['datetime']
df['lapsetime (minutes)'] = (df['lapsetime (minutes)'].dt.total_seconds() / 60).round(2)
df['title'] = [f'Tanggal: {d} {t}, Mag: {m}, Depth: {dp}' for d, t, m, dp in zip(dates, times, mags, depths)]

# --- Date Filtering ---
try:
    start_dt = pd.to_datetime(time_sta, errors='coerce')
    end_dt   = pd.to_datetime(time_end, errors='coerce')
    filtered = df[(df['datetime'] >= start_dt) & (df['datetime'] <= end_dt)].copy()
except Exception:
    st.warning("🧭 Format waktu tidak valid. Pastikan input sesuai contoh: YYYY-MM-DD HH:MM:SS")
    filtered = pd.DataFrame()

# --- Interactive Map ---
tiles = 'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
map_obj = folium.Map(location=[-4, 118], tiles=tiles, attr='ESRI', zoom_start=4.5)

if not filtered.empty:
    for lat, lon, title in zip(filtered['lat'], filtered['lon'], filtered['title']):
        folium.Marker([lat, lon], popup=title, icon=folium.Icon(color='red')).add_to(map_obj)

st.markdown("### Seismisitas 30 Kejadian Gempabumi terakhir (BMKG)")
st_folium(map_obj, width=1000)

# --- Chart & Table Display ---
st.markdown("### Grafik Kecepatan Diseminasi Gempabumi M >=5")

threshold = 3.0
df_filtered = filtered.copy()

if not df_filtered.empty:
    df_filtered['flag'] = df_filtered['lapsetime (minutes)'].astype(float) > threshold

    base = alt.Chart(df_filtered).encode(
        x='datetime:T',
        y='lapsetime (minutes):Q'
    )

    circles = base.transform_filter('datum.flag == false').mark_circle(size=60, color='blue')
    crosses = base.transform_filter('datum.flag == true').mark_point(
        shape='cross', color='red', size=80, strokeWidth=2
    )
    rule = alt.Chart(pd.DataFrame({'y': [threshold]})).mark_rule(
        color='gray', strokeDash=[6, 3]
    ).encode(y='y:Q')

    st.altair_chart(circles + crosses + rule, use_container_width=True)

st.markdown("### KECEPATAN PENYAMPAIAN INFORMASI PERINGATAN DINI TSUNAMI AKIBAT GEMPABUMI")
st.markdown(f"### 🕒 Periode Monitoring: `{time_sta}` s.d. `{time_end}`")

if not filtered.empty:
    df_show = filtered.copy()
    df_show['Date'] = df_show['datetime'].dt.strftime('%d-%b-%y')
    df_show['OT'] = df_show['datetime'].dt.strftime('%H:%M:%S')
    df_show['Diss Time'] = df_show['timesent'].dt.strftime('%H:%M:%S')
    df_show['Diss Time-OT'] = df_show['lapsetime (minutes)'].apply(minutes_to_hms)

    df_show.rename(columns={
        'mag': 'Mag Diss',
        'depth': 'Depth-Diss (Km)',
        'area': 'Lokasi'
    }, inplace=True)

    df_display = df_show[['Date', 'OT', 'Diss Time', 'Diss Time-OT', 'Lat-Diss', 'Lon-Diss', 'Mag Diss', 'Depth-Diss (Km)', 'Lokasi']]
    df_display.index = range(1, len(df_display) + 1)
    st.dataframe(df_display)
else:
    st.info("Tidak ada data gempabumi pada rentang waktu terpilih.")
