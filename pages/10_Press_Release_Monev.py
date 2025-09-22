import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import datetime

# 🌐 Page Config
st.set_page_config(page_title='Earthquake Press Releases', layout='wide', page_icon='📰')

# 📅 Time Filter
st.sidebar.header("Time Range Filter")
time_start_str = st.sidebar.text_input('Start DateTime:', '2025-07-01 00:00:00')
time_end_str   = st.sidebar.text_input('End DateTime:', '2025-07-30 23:59:59')

try:
    time_start = pd.to_datetime(time_start_str)
    time_end   = pd.to_datetime(time_end_str)
except Exception:
    st.error("❌ Invalid datetime format. Please use YYYY-MM-DD HH:MM:SS")
    st.stop()

# --- Helper Functions ---
def extract_text(tag):
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
        return soup.get_text(separator="\n", strip=True)
    return None

def build_narasi_dataframe(df, time_col="time_narasi"):
    df["narasi_html"] = df[time_col].apply(fetch_narasi_text)
    df["narasi_text"] = df["narasi_html"].apply(html_to_text)
    return df

# --- Fetch and Parse XML ---
url = 'https://bmkg-content-inatews.storage.googleapis.com/last30event.xml'
soup = BeautifulSoup(requests.get(url).text, 'html')
timesent = extract_text('timesent')

# --- Build DataFrame ---
df = pd.DataFrame({'timesent': [parse_timesent(ts) for ts in timesent]})
df = convert_datetime_column(df, "timesent", "time_narasi")
df = build_narasi_dataframe(df, time_col="time_narasi")

# --- Filter by Time Range ---
df['timesent'] = pd.to_datetime(df['timesent'], errors='coerce')
df = df[df['timesent'].notna()]
df = df[(df['timesent'] >= time_start) & (df['timesent'] <= time_end)]

# 📈 Message Count
st.markdown(f"### 📈 Total Messages: **{len(df)}** between `{time_start}` and `{time_end}`")

# 🧾 Styled Table View
st.subheader("🧾 Press Release InaTEWS Table View")
df_display = df[["timesent", "narasi_text"]].copy()
df_display.index = range(1, len(df_display) + 1)
#st.dataframe(df_display)
#st.table(df_display)

# Build styled HTML table with 3 columns
styled_table = """
<style>
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
    }
    th, td {
        border: 1px solid #ccc;
        padding: 6px 10px;
        text-align: left;
        vertical-align: top;
    }
    th {
        background-color: #f0f0f0;
    }
    td:nth-child(1) { width: 8%; }   /* Index column */
    td:nth-child(2) { width: 22%; }  /* Time Sent */
    td:nth-child(3) { width: 70%; }  /* Narasi Text */
</style>
<table>
    <thead>
        <tr>
            <th>No</th>
            <th>Time Sent</th>
            <th>Narasi Text</th>
        </tr>
    </thead>
    <tbody>
"""

# Populate rows
for i, row in df_display.iterrows():
    styled_table += f"""
        <tr>
            <td>{i}</td>
            <td>{row['timesent']}</td>
            <td>{row['narasi_text']}</td>
        </tr>
    """

styled_table += """
    </tbody>
</table>
"""

# Render the styled table
st.markdown(styled_table, unsafe_allow_html=True)


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

pdf_data = generate_pdf(df_display)
st.download_button(
    label="📄 Download Press Releases as PDF",
    data=pdf_data,
    file_name="press_releases.pdf",
    mime="application/pdf"
)
