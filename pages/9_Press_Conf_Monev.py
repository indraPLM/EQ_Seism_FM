import streamlit as st
import pandas as pd


# 🌍 Page Config
st.set_page_config(page_title='Earthquake Dashboard', layout='wide', page_icon='🌋')

# 🛠️ Sidebar Inputs
st.sidebar.header("Input Parameters")
time_start = st.sidebar.text_input('Start Time', '2025-01-01 00:00:00')
time_end   = st.sidebar.text_input('End Time', '2025-05-30 23:59:59')

# === Page setup ===
st.set_page_config(page_title="Filtered Earthquake Messages", layout="wide")
st.title("📄 Filtered Messages Viewer")
st.markdown("Displaying messages containing **Dr. Daryono**, filtered by time range.")

# === Load data ===
csv_file = "./pages/filePressConf/filtered_messages.csv"
try:
    df = pd.read_csv(csv_file)
    df['date'] = pd.to_datetime(df['date'])

    # === Filter data ===
    if time_start <= time_end:
        filtered_df = df[(df['date'] >= time_start) & (df['date'] <= time_end)]
        st.dataframe(filtered_df, use_container_width=True)
        st.success(f"🕓 Showing {len(filtered_df)} messages from {time_start} to {time_end}")
    else:
        st.warning("⚠️ Start time must be before end time.")

except FileNotFoundError:
    st.error(f"CSV file '{csv_file}' not found. Please check the file path.")
