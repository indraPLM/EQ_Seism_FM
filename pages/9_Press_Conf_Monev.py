import streamlit as st
import pandas as pd

# === Page setup ===
st.set_page_config(page_title="Filtered Earthquake Messages", layout="wide")
st.title("📄 Filtered Messages Viewer")
st.markdown("Displaying messages containing **Dr. Daryono**, filtered by time range.")

# === Load data ===
csv_file = "filtered_messages.csv"
try:
    df = pd.read_csv(csv_file)
    df['date'] = pd.to_datetime(df['date'])

    # === Sidebar datetime inputs ===
    st.sidebar.header("🗓️ Time Filter")
    min_datetime = df['date'].min()
    max_datetime = df['date'].max()

    start = st.sidebar.datetime_input("Start Date & Time:", value=min_datetime, min_value=min_datetime, max_value=max_datetime)
    end = st.sidebar.datetime_input("End Date & Time:", value=max_datetime, min_value=min_datetime, max_value=max_datetime)

    # === Filter data ===
    if start <= end:
        filtered_df = df[(df['date'] >= start) & (df['date'] <= end)]
        st.dataframe(filtered_df, use_container_width=True)
        st.success(f"🕓 Showing {len(filtered_df)} messages from {start} to {end}")
    else:
        st.warning("⚠️ Start time must be before end time.")

except FileNotFoundError:
    st.error(f"CSV file '{csv_file}' not found. Please check the file path.")
