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

def fetch_messages():
    try:
        client.start()
        channel = client.get_entity(channel_username)
        messages = client.iter_messages(channel, limit=500)

        filtered_data = [
            {
                'date': msg.date,
                'sender_id': msg.sender_id,
                'message': msg.text
            }
            for msg in messages
            if msg.text and keyword.lower() in msg.text.lower()
        ]

        if filtered_data:
            df = pd.DataFrame(filtered_data)
            df.to_csv('daryono_messages.csv', index=False, encoding='utf-8')
            print(f"Saved {len(filtered_data)} messages to CSV.")
        else:
            print("No matching messages found.")

    except SessionPasswordNeededError:
        print("Two-step verification required.")
    except Exception as e:
        print(f"Error: {e}")

with client:
    fetch_messages()
st.dataframe(df)
