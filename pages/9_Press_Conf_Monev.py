import streamlit as st
import pandas as pd

# 🌐 Page Configuration
st.set_page_config(page_title='Earthquake Press Releases', layout='wide', page_icon='📰')

# 📅 Sidebar Time Filter
st.sidebar.header("Time Range Filter")
time_start = st.sidebar.text_input('Start Time (YYYY-MM-DD HH:MM:SS)', '2025-01-01 00:00:00')
time_end   = st.sidebar.text_input('End Time (YYYY-MM-DD HH:MM:SS)', '2025-05-30 23:59:59')

# 📂 Load and Prep Data
csv_file = "./pages/filePressConf/filtered_messages.csv"
try:
    df = pd.read_csv(csv_file)
    df['date'] = pd.to_datetime(df['date'])

    # ⏰ Format Columns
    df['Tanggal Waktu'] = df['date'].dt.strftime('%d-%b-%y %H:%M:%S')
    df['Press Release Message'] = df['message']

    # 🧭 Filter by Time Range
    start_dt = pd.to_datetime(time_start).tz_localize('UTC')
    end_dt = pd.to_datetime(time_end).tz_localize('UTC')
    filtered_df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)].copy()

    # 🔢 Add Row Numbers
    filtered_df.reset_index(drop=True, inplace=True)
    filtered_df.index += 1
    filtered_df['No'] = filtered_df.index

    # 🎛 Select Display Columns
    final_df = filtered_df[['No', 'Tanggal Waktu', 'Press Release Message']]

    # 📊 First Show in Interactive DataFrame
    st.subheader("🔍 Interactive View")
    st.dataframe(final_df, use_container_width=True)

    # 🧾 Then Show as Styled Table
    st.subheader("🧾 Styled Table View")
    st.write('<style>th, td { padding: 10px; vertical-align: top; word-wrap: break-word; max-width: 600px; }</style>', unsafe_allow_html=True)
    st.table(final_df)

    st.success(f"✅ Displayed {len(final_df)} messages between {time_start} and {time_end}")

except FileNotFoundError:
    st.error(f"❌ File not found: '{csv_file}'")
except Exception as e:
    st.error(f"💥 Unexpected error: {e}")
