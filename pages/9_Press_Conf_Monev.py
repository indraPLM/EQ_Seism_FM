import streamlit as st
import pandas as pd

# ✅ Page Configuration (only once, first)
st.set_page_config(page_title='Earthquake Dashboard', layout='wide', page_icon='📰')


# 🛠️ Sidebar Inputs
st.sidebar.header("📅 Time Range Filter")
time_start = st.sidebar.text_input('Start Time (YYYY-MM-DD HH:MM:SS)', '2025-01-01 00:00:00')
time_end = st.sidebar.text_input('End Time (YYYY-MM-DD HH:MM:SS)', '2025-05-30 23:59:59')

# 🧭 Page Setup
st.title("📄 Press Release Messages InaTEWS")
st.markdown("Displaying **Press Release Messages** from InaTEWS")

# 📂 Load CSV Data
csv_file = "./pages/filePressConf/filtered_messages.csv"
try:
    df = pd.read_csv(csv_file)
    df['date'] = pd.to_datetime(df['date'])

    # 🧮 Add Formatted Columns and Rename
    df['Tanggal'] = df['date'].dt.strftime('%d-%b-%y')
    df['Waktu'] = df['date'].dt.strftime('%H:%M:%S')
    df['Press Release Message'] = df['message']

    # ⏳ Filter Based on Time Input
    if time_start <= time_end:
        start_dt = pd.to_datetime(time_start)
        end_dt = pd.to_datetime(time_end)
        filtered_df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)].copy()

        # 🔢 Add Sequential Numbering Starting from 1
        filtered_df.reset_index(drop=True, inplace=True)
        filtered_df.index += 1
        filtered_df['No'] = filtered_df.index

        # 📊 Select Columns for Display
        final_df = filtered_df[['No', 'Tanggal', 'Waktu', 'Press Release Message']]
        st.dataframe(final_df, use_container_width=True)
        st.success(f"🕓 Showing {len(final_df)} messages from {start_dt} to {end_dt}")
    else:
        st.warning("⚠️ Start time must be before end time.")

except FileNotFoundError:
    st.error(f"❌ CSV file '{csv_file}' not found. Please verify the path.")
except Exception as e:
    st.error(f"💥 Unexpected error: {e}"
