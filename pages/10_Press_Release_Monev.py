import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import datetime
from re import findall, sub
from math import hypot

# 🌐 Page Config
st.set_page_config(page_title='Earthquake Press Releases', layout='wide', page_icon='📰')

# 📅 Time Filter
st.sidebar.header("Time Range Filter")
time_start_str = st.sidebar.text_input(
    'Start DateTime:',
    datetime.datetime.today().strftime("%Y-%m-01 00:00:00")
)
time_end_str = st.sidebar.text_input(
    'End DateTime:',
    datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
)

try:
    time_start = pd.to_datetime(time_start_str)
    time_end   = pd.to_datetime(time_end_str)
except Exception:
    st.error("❌ Invalid datetime format. Please use YYYY-MM-DD HH:MM:SS")
    st.stop()

# --- Helper Functions ---
def extract_text(tag, soup):
    return [t.text.strip() for t in soup.find_all(tag)]

def parse_timesent(ts):
    ts = ts.strip().replace('WIB','').replace('UTC','')
    for fmt in ["%d/%m/%Y %H:%M:%S", "%d-%b-%y %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
        try:
            return pd.to_datetime(ts, format=fmt)
        except:
            continue
    return pd.NaT

def convert_datetime_column(df, source_col, target_col):
    df[target_col] = df[source_col].apply(
        lambda x: x.strftime("%Y%m%d%H%M%S") if pd.notnull(x) else None
    )
    return df

def fetch_narasi_text(time_narasi):
    url = f"https://bmkg-content-inatews.storage.googleapis.com/{time_narasi}_narasi.txt"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except Exception:
        return None

def html_to_text(html_content):
    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        from re import sub
        return sub(
            r"(?<=\W) (?=\W)",
            "",
            sub(
                r"((?<=\W)\n)|(\n(?=TIDAK BERPOTENSI TSUNAMI))",
                " ",
                sub(
                    r"((?<=\()\n)|(\n(?=\W))",
                    "",
                    soup.get_text(separator="\n", strip=True)
                )
            )
        )
    return None

def build_narasi_dataframe(df, time_col="time_narasi"):
    df["narasi_html"] = df[time_col].apply(fetch_narasi_text)
    df["narasi_text"] = df["narasi_html"].apply(html_to_text)
    return df


# COLUMN NAMES!
tim_co0 = "timesent"
nar_co0 = "narasi_text"

# --- Fetch and Parse XML ---
url_pre = 'https://bmkg-content-inatews.storage.googleapis.com/last30event.xml'
sou_pre = BeautifulSoup(requests.get(url_pre).text, 'html')
tim_pre = extract_text(tim_co0, sou_pre)

# --- Build DataFrame ---
df = pd.DataFrame({
    tim_co0: [parse_timesent(n) for n in tim_pre]
}).sort_values(by=tim_co0)
df = convert_datetime_column(df, tim_co0, "time_narasi")
df = build_narasi_dataframe(df, time_col="time_narasi")

# --- Filter by Time Range ---
# df['timesent'] = pd.to_datetime(df['timesent'], errors='coerce')
df = df[df[tim_co0].notna()]
df = df[(df[tim_co0] >= time_start) & (df[tim_co0] <= time_end)]

# 📈 Message Count
st.markdown(f"### 📈 Total Messages: **{len(df)}** between `{time_start}` and `{time_end}`")

# COLUMN NAMES!
ind_co1 = "№"
tim_co1 = "Time Sent"
lat_co1 = "Latitude (°N)"
lon_co1 = "Longitude (°E)"
dep_co1 = "Depth (km)"
mag_co1 = "Magnitude"
nar_co1 = "Narration Text"


def lat_ett(data: pd.DataFrame):
    return [[(-1 if o[-1] == "S" else 1) * float(
        sub(r"° L.", "", o).replace(",", ".")
    ) for o in findall(r"[^ ]+ L[US]", n)][0] for n in data[nar_co0].tolist()]


def lon_ett(data: pd.DataFrame):
    return [[(-1 if o[-1] == "B" else 1) * float(
        sub(r"° B.", "", o).replace(",", ".")
    ) for o in findall(r"[^ ]+ B[TB]", n)][0] for n in data[nar_co0].tolist()]


def dep_ett(data: pd.DataFrame):
    return [
        float(findall(r"(?<=kedalaman )[^ ]+(?= km)", n)[0].replace(",", "."))
        for n in data[nar_co0].tolist()
    ]


def mag_ett(data: pd.DataFrame):
    return [
        float((findall(r"magnitudo M?(?=([^.]+))", n))[0].replace(",", "."))
        for n in data[nar_co0].tolist()
    ]


# PARSING!
df.insert(1, lat_co1, lat_ett(df))
df.insert(2, lon_co1, lon_ett(df))
df.insert(3, dep_co1, dep_ett(df))
df.insert(4, mag_co1, mag_ett(df))

# 🧾 Styled Table View
st.subheader("🧾 Press Release InaTEWS Table View")
df_display = df.copy().drop(columns=["time_narasi", "narasi_html"])
df_display.index = range(1, len(df_display) + 1)
df_display.reset_index(inplace=True)
df_display.rename(columns={
    "index": ind_co1,
    tim_co0: tim_co1,
    nar_co0: nar_co1
}, inplace=True)

# Display using st.table
st.dataframe(df_display, hide_index=True)


# 📤 PDF Export Function
def generate_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Earthquake Press Releases", ln=True, align="C")
    pdf.ln(5)

    for idx, row in df.iterrows():
        text = f"{idx}. {row['timesent']} - {row['narasi_text']}"
        pdf.multi_cell(0, 8, txt=text)
        pdf.ln(1)

    buffer = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer.write(pdf_bytes)
    buffer.seek(0)
    return buffer

pdf_data = generate_pdf(df)
st.download_button(
    label="📄 Download Press Releases as PDF",
    data=pdf_data,
    file_name="press_releases.pdf",
    mime="application/pdf"
)


def lat_prs(lat):
    return -float(lat.replace('LS', '').strip()) \
        if 'LS' in lat \
        else float(lat.replace('LU', '').strip())


def lon_prs(lon):
    return -float(lon.replace('BB', '').strip()) \
        if 'BB' in lon \
        else float(lon.replace('BT', '').strip())


def dep_prs(dep):
    return float(sub(r" [Kk]m", "", dep))


# COLUMN NAMES!
lat_co2 = "Dis y (°N)"
lon_co2 = "Dis x (°E)"
dep_co2 = "Dis z (km)"
mag_co2 = "Dis M"
lat_co3 = "Pre y (°N)"
lon_co3 = "Pre x (°E)"
dep_co3 = "Pre z (km)"
mag_co3 = "Pre M"

# COMPARISONS!
st.subheader("🧾 Dissemination vs. Press Release Parameter Comparison")
url_dis = 'https://bmkg-content-inatews.storage.googleapis.com/last30event.xml'
sou_dis = BeautifulSoup(requests.get(url_dis).text, 'html')
dtf_dis = pd.merge(
    left=pd.DataFrame({
        tim_co1: [parse_timesent(n) for n in extract_text(tim_co0, sou_dis)],
        lat_co2: [lat_prs(n) for n in extract_text('latitude', sou_dis)],
        lon_co2: [lon_prs(n) for n in extract_text('longitude', sou_dis)],
        dep_co2: [dep_prs(n) for n in extract_text('depth', sou_dis)],
        mag_co2: [float(n) for n in extract_text('magnitude', sou_dis)],
    }),
    right=df_display.rename(columns={
        lat_co1: lat_co3,
        lon_co1: lon_co3,
        dep_co1: dep_co3,
        mag_co1: mag_co3
    }).drop(columns=[nar_co1]),
    on=tim_co1
).sort_values(by=tim_co1)
idc_dis = dtf_dis.pop(ind_co1)
dtf_dis.insert(0, ind_co1, idc_dis)
dtf_dis["Dif d (km)"] = [hypot(m, n) * 111 for m, n in zip(
    dtf_dis[lat_co2] - dtf_dis[lat_co3],
    dtf_dis[lon_co2] - dtf_dis[lon_co3]
)]
dtf_dis["Dif z (km)"] = (dtf_dis[dep_co2] - dtf_dis[dep_co3]).apply(abs)
dtf_dis["Dif M (km)"] = (dtf_dis[mag_co2] - dtf_dis[mag_co3]).apply(abs)
st.dataframe(dtf_dis, hide_index=True)
