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
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# --- Scraping function using Selenium ---
def get_messages():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://t.me/s/InaTEWS_BMKG")
    time.sleep(5)  # Let the page load

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    raw_msgs = soup.find_all("div", class_="tgme_widget_message_text")
    messages = [msg.get_text(strip=True) for msg in raw_msgs]
    return messages

# --- Streamlit dashboard ---
st.set_page_config(page_title="InaTEWS Live Feed", layout="wide")
st.title("🌋 InaTEWS BMKG – Live Telegram Feed")

st.sidebar.subheader("🔄 Refresh Settings")
interval = st.sidebar.slider("Refresh every N seconds", min_value=30, max_value=600, value=120, step=30)

msg_display = st.empty()
last_updated = st.sidebar.empty()

while True:
    with st.spinner("Scraping messages..."):
        messages = get_messages()

    msg_display.markdown("### 📨 Latest Messages:")
    for i, msg in enumerate(messages[:20], 1):  # Limit to last 20 messages
        st.write(f"{i}. {msg}")

    last_updated.info(f"Last updated at ⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(interval)
    st.rerun()
