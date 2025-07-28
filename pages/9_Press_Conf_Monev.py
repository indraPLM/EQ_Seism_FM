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
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from streamlit_autorefresh import st_autorefresh

# === Telegram Credentials ===
api_id = '22270251'
api_hash = '44dc58cc1db11f47cf3de0f28d6a8786'
channel_username = 'BMKGAlertViewer'
session_name = 'bmkgviewer'

# === Auto-refresh every 60 seconds ===
st_autorefresh(interval=60000, limit=None, key="bmkg_refresh")

# === Streamlit UI ===
st.title("🌋 BMKG InaTEWS Telegram Monitor")
st.caption("Fetching latest earthquake & tsunami alerts from @InaTEWS_BMKG")

try:
    with TelegramClient(session_name, api_id, api_hash) as client:
        messages = []
        for message in client.iter_messages(channel_username, limit=20):
            if message.text:
                msg_time = message.date.strftime('%Y-%m-%d %H:%M:%S')
                messages.append(f"[{msg_time}] {message.text}")

        for msg in messages:
            st.text(msg)

except SessionPasswordNeededError:
    st.error("Two-factor auth enabled — please provide your password in the script.")
except Exception as e:
    st.error(f"Error: {e}")
