import streamlit as st
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Globals to store incoming messages
messages = []

# Telegram Bot Setup
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello from Streamlit bot!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    sender = update.effective_user.username or update.effective_user.first_name
    messages.append(f"{sender}: {user_msg}")
    await update.message.reply_text(f"Got it: {user_msg}")

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()

# Start Telegram bot in background
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

# Streamlit UI
st.title("📨 Telegram Bot Message Viewer")
st.write("Messages received via Telegram:")

# Live update of messages
if st.button("Refresh Messages"):
    st.rerun()

for msg in messages[-20:]:  # Show last 20 messages
    st.write(msg)


import streamlit as st
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from streamlit_autorefresh import st_autorefresh

# ========== USER CONFIGURATION ==========
api_id = 22270251              # Replace with your numeric API ID
api_hash = '44dc58cc1db11f47cf3de0f28d6a8786'         # Replace with your API hash string
channel_username = 'BMKGAlertViewer'  # Telegram channel name (without @)
session_name = 'bmkgviewer'     # Session name for login persistence

# ========== STREAMLIT SETTINGS ==========
st.set_page_config(page_title="BMKG InaTEWS Monitor", layout="wide")
st.title("🌋 BMKG InaTEWS Telegram Monitor")
st.caption("Live feed from @InaTEWS_BMKG — earthquake & tsunami alerts")

# ========== STREAMLIT SETUP ==========
#st.set_page_config(page_title="BMKG Alert Stream", layout="centered")
#st.title("🌋 BMKG Telegram Alert Monitor")
#st.caption("Highlighting mentions of Dr. Daryono in latest alerts")

# Sidebar: Refresh interval
st.sidebar.header("🔄 Auto-Refresh Settings")
refresh_interval = st.sidebar.slider("Refresh every (seconds)", 30, 300, 60, step=30)
st_autorefresh(interval=refresh_interval * 1000, key="auto_refresh")

# ========== TELEGRAM FETCH ==========
async def fetch_latest_message():
    try:
        async with TelegramClient(session_name, api_id, api_hash) as client:
            async for msg in client.iter_messages(channel_username, limit=1):
                if msg.text:
                    timestamp = msg.date.strftime("%Y-%m-%d %H:%M:%S")
                    text = msg.text

                    # Keyword highlighting
                    keyword = "Dr. DARYONO, S.Si., M.Si."
                    if keyword in text:
                        text = text.replace(keyword, f"**🧠 {keyword}**")
                        tagged = True
                    else:
                        tagged = False

                    return f"🕒 {timestamp}\n\n{text}", tagged
            return "No recent text message found.", False
    except SessionPasswordNeededError:
        return "❗ Two-factor authentication is required.", False
    except Exception as e:
        return f"❗ Error fetching message: {e}", False

# ========== DISPLAY ==========
with st.spinner("📡 Checking BMKG feed..."):
    try:
        latest_message, tagged = asyncio.run(fetch_latest_message())
        st.text_area("📨 Latest Telegram Message", latest_message, height=400)

        if tagged:
            st.success("🔍 Tagged alert: Dr. Daryono mentioned in this message.")
        else:
            st.info("ℹ️ No mention of Dr. Daryono in this update.")

    except RuntimeError as e:
        st.error(f"Runtime error: {e}")
