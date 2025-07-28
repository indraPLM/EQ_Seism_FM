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

# Sidebar refresh settings
st.sidebar.header("⏱️ Refresh Controls")
refresh_interval = st.sidebar.slider("Auto-refresh every (seconds)", 30, 600, 120, step=30)

# Trigger auto-refresh via streamlit-autorefresh
st_autorefresh(interval=refresh_interval * 1000, key="refresh_counter")

# ========== TELEGRAM SCRAPE FUNCTION ==========
async def fetch_messages():
    try:
        async with TelegramClient(session_name, api_id, api_hash) as client:
            messages = []
            async for msg in client.iter_messages(channel_username, limit=20):
                if msg.text:
                    timestamp = msg.date.strftime("%Y-%m-%d %H:%M:%S")
                    messages.append(f"[{timestamp}] {msg.text}")
            return messages
    except SessionPasswordNeededError:
        return ["❗ Two-factor authentication enabled — update your script."]
    except Exception as e:
        return [f"❗ Error occurred: {e}"]

# ========== RUN ASYNC + DISPLAY ==========
with st.spinner("📡 Fetching Telegram messages..."):
    try:
        messages = asyncio.run(fetch_messages())
        for i, msg in enumerate(messages, 1):
            st.write(f"{i}. {msg}")
    except RuntimeError as e:
        st.error(f"Runtime error: {e}")

