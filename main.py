import asyncio
import time
import os
from datetime import datetime, time as dtime


import yfinance as yf
from telegram import Bot

from dotenv import load_dotenv

# Telegram bot token and chat ID
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
STOCK_SYMBOLS = os.environ.get("STOCK_SYMBOLS", "AAPL").split(
    ","
)  # Example: Apple stock

print(f"Stocks to monitor: {STOCK_SYMBOLS}")
# Initialize Telegram bot
bot = Bot(token=BOT_TOKEN)
last_summary_sent_date = None  # Track last summary date


# Stock symbol and threshold for the price drop
THRESHOLD_DROP = 5.0  # 5% drop
MA_WINDOW = 200  # 200-day moving average
SLEEP_TIME = 60  # seconds


# Function to get current stock price
def get_stock_price(symbol, ma_window=MA_WINDOW):
    try:
        # Fetch historical data
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")  # 1 year for 200-day MA

        if len(hist) < ma_window:
            print("Not enough data to calculate 200-day MA.")
            return

        ma200 = hist["Close"].rolling(window=ma_window).mean().iloc[-1]
        current_price = hist["Close"].iloc[-1]
        previous_close = hist["Close"].iloc[-2]

        return current_price, previous_close, ma200
    except Exception as e:
        print(f"Error checking stock: {e}")


# Function to send notification to Telegram
async def send_notification(message):
    await bot.send_message(chat_id=CHAT_ID, text=message)


async def send_daily_summary():
    summary_lines = ["📊 Daily Stock Summary:"]
    for stock in STOCK_SYMBOLS:
        try:
            current_price, previous_close, ma200 = get_stock_price(stock)
            drop_percentage = ((previous_close - current_price) / previous_close) * 100

            line = (
                f"{stock}:\n"
                f"  - Current: USD${current_price:.2f}\n"
                f"  - Prev Close: USD${previous_close:.2f}\n"
                f"  - 200MA: USD${ma200:.2f}\n"
                f"  - Drop: {drop_percentage:.2f}%\n"
            )
            summary_lines.append(line)
        except Exception as e:
            summary_lines.append(f"{stock}: Error fetching data – {e}")

    await send_notification("\n".join(summary_lines))


# Monitoring function
async def monitor_stock():
    global last_summary_sent_date
    print("Start monitoring stocks...")

    while True:
        now = datetime.now()

        for stock in STOCK_SYMBOLS:
            try:
                current_price, previous_close, ma200 = get_stock_price(stock)
                drop_percentage = (
                    (previous_close - current_price) / previous_close
                ) * 100

                print(
                    f"[INFO] {now.isoformat()} {stock}: Current ${current_price:.2f}, Prev ${previous_close:.2f}, 200MA ${ma200:.2f}, Drop {drop_percentage:.2f}%"
                )

                if current_price < ma200 and drop_percentage >= THRESHOLD_DROP:
                    message = (
                        f"⚠️ {stock} dropped below its 200-day MA and more than {THRESHOLD_DROP}% from previous close!\n"
                        f"Current: USD${current_price:.2f}\n"
                        f"Prev Close: USD${previous_close:.2f}\n"
                        f"200-day MA: USD${ma200:.2f}\n"
                        f"Drop: {drop_percentage:.2f}%"
                    )
                    await send_notification(message)
                else:
                    print(f"[INFO] {stock} OK – No alert condition met.")
            except Exception as e:
                print(f"[ERROR] Failed to check {stock}: {e}")

        # Send daily summary at 16:30 (or anytime after that, once per day)
        summary_target_time = dtime(hour=21, minute=30)
        if now.time() >= summary_target_time and (
            last_summary_sent_date is None or last_summary_sent_date.date() < now.date()
        ):
            print("[INFO] Sending daily summary...")
            await send_daily_summary()
            last_summary_sent_date = now

        time.sleep(SLEEP_TIME)


if __name__ == "__main__":
    asyncio.run(monitor_stock())
