import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import folium
from streamlit_folium import st_folium
import datetime

# 🌐 Page Config
st.set_page_config(page_title='Earthquake Press Releases', layout='wide', page_icon='📰')

# 📅 Time Filter
st.sidebar.header("Time Range Filter")
time_start = st.sidebar.text_input('Start DateTime:', '2025-06-01 00:00:00')
time_end   = st.sidebar.text_input('End DateTime:', '2025-06-30 23:59:59')

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
    'Lat-Diss':lats,
    'Lon-Diss':lons,
    'mag': mags,
    'depth': depths
})

dates     = extract_text('date')
times     = extract_text('time')
df['date']=dates
df['time']=times
st.dataframe(df)


# 📂 Load Data
csv_file = "./pages/filePressConf/filtered_messages.csv"
try:
    df = pd.read_csv(csv_file)
    df['date'] = pd.to_datetime(df['date'])
    df['Tanggal'] = df['date'].dt.strftime('%d-%b-%y')
    df['Waktu'] = df['date'].dt.strftime('%H:%M:%S')
    df['Press Release Message'] = df['message']

    # 🧭 Filter Time Range
    start_dt = pd.to_datetime(time_start).tz_localize('UTC')
    end_dt = pd.to_datetime(time_end).tz_localize('UTC')
    filtered_df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)].copy()

    # 🔢 Row Numbers
    filtered_df.reset_index(drop=True, inplace=True)
    filtered_df.index += 1
    filtered_df['No'] = filtered_df.index

    # 🧾 Final Table
    final_df = filtered_df[['No', 'Tanggal', 'Waktu', 'Press Release Message']]

    # 🔍 Interactive View
    st.subheader("🔍 Press Release InaTEWS Interactive View")
    st.dataframe(final_df, use_container_width=True)

    # 📈 Message Count
    st.markdown(f"### 📈 Total Messages: **{len(final_df)}** between `{time_start}` and `{time_end}`")

    # 🧾 Styled Table View
    st.subheader("🧾 Press Release InaTEWS Table View")
    st.write('<style>th, td { padding: 10px; vertical-align: top; word-wrap: break-word; max-width: 600px; }</style>', unsafe_allow_html=True)
    st.table(final_df)

    # 📤 PDF Export Function
    def generate_pdf(df):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt="Earthquake Press Releases", ln=True, align="C")
        pdf.ln(5)

        for index, row in df.iterrows():
            text = f"{row['No']}. {row['Tanggal']} {row['Waktu']} - {row['Press Release Message']}"
            pdf.multi_cell(0, 8, txt=text)
            pdf.ln(1)

        buffer = BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin1')  # Returns string, encode to bytes
        buffer.write(pdf_bytes)
        buffer.seek(0)
        return buffer

    pdf_data = generate_pdf(final_df)
    st.download_button(
        label="📄 Download Press Releases as PDF",
        data=pdf_data,
        file_name="press_releases.pdf",
        mime="application/pdf"
    )

except FileNotFoundError:
    st.error(f"❌ File not found: '{csv_file}'")
except Exception as e:
    st.error(f"💥 Unexpected error: {e}")
