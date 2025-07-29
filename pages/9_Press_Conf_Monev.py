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


import asyncio
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
import pandas as pd

# Telegram API credentials
api_id = 22270251
api_hash = '44dc58cc1db11f47cf3de0f28d6a8786'
keyword = "Dr. Daryono, S.Si, M.Si"
channel_username = 'BMKGAlertViewer'

# Create a new event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient('bmkgviewer', api_id, api_hash, loop=loop)

import asyncio
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest

# === UI: Manual credential input ===
st.title("🔎 Telegram Message Grabber")
st.subheader("Search messages from any public Telegram channel")

api_id = 22270251
api_hash = '44dc58cc1db11f47cf3de0f28d6a8786'
phone = '+6281280371045'
session_name = 'bmkgviewer'
channel_name = 'InaTEWS_BMKG'
keyword = "Dr. DARYONO, S.Si., M.Si."

start_date = st.date_input("Start date", value=datetime(2025, 1, 1))
end_date = st.date_input("End date", value=datetime.now())

# === Run on button click ===
if st.button("Grab Messages") and api_id and api_hash and phone and session_name:
    api_id = int(api_id.strip())
    client = TelegramClient(session_name, api_id, api_hash.strip())

    async def fetch_messages():
        await client.start()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            code = st.text_input("Enter the code you received in Telegram")
            password = st.text_input("Telegram 2FA password (if applicable)", type="password")
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                await client.sign_in(password=password)

        channel = await client.get_entity(channel_name)
        all_messages = []
        offset_id = 0
        total_fetched = 0
        st.info("Fetching messages...")
        progress = st.progress(0)

        while True:
            history = await client(GetHistoryRequest(
                peer=channel,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=100,
                max_id=0,
                min_id=0,
                hash=0
            ))
            if not history.messages:
                break

            for msg in history.messages:
                if msg.message:
                    msg_date = msg.date.date()
                    if keyword.lower() in msg.message.lower() and start_date <= msg_date <= end_date:
                        all_messages.append({
                            "date": msg.date.isoformat(),
                            "message": msg.message
                        })

            offset_id = history.messages[-1].id
            total_fetched += len(history.messages)
            progress.progress(min(total_fetched / 500, 1.0))
            if total_fetched >= 500:
                break

        return all_messages

    with client:
        results = asyncio.run(fetch_messages())
        if results:
            df = pd.DataFrame(results)
            st.success(f"Found {len(df)} matching messages.")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            json_data = json.dumps(results, indent=2)

            st.download_button("⬇ Download CSV", csv, file_name="messages.csv", mime="text/csv")
            st.download_button("⬇ Download JSON", json_data, file_name="messages.json", mime="application/json")
        else:
            st.warning("No messages found for the given keyword and date range.")
else:
    st.info("Please enter your Telegram credentials above to begin.")

