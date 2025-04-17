import asyncio
import time
import os

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

print(STOCK_SYMBOLS)
# Initialize Telegram bot
bot = Bot(token=BOT_TOKEN)

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


# Monitoring function
async def monitor_stock():
    print("Start monitoring stocks...")
    while True:
        for stock in STOCK_SYMBOLS:
            current_price, previous_close, ma200 = get_stock_price(stock)

            # calculate percentage drop
            drop_percentage = ((previous_close - current_price) / previous_close) * 100

            print(
                f"[INFO] EpochTime: {time.time():.2f} Current {stock} price: {current_price:.2f}, Previous close: {previous_close:.2f}, 200MA: {ma200:.2f}, Previous Close vs Current Price: {drop_percentage:.2f}%"
            )

            if current_price < ma200 and drop_percentage >= THRESHOLD_DROP:
                message = (
                    f"⚠️ {stock} dropped below its 200-day MA and is more {THRESHOLD_DROP}% drop from previous day close!\n"
                    f"Current Price: USD${current_price:.2f}\n"
                    f"Previous Close: USD${previous_close:.2f}\n"
                    f"200-day MA: USD${ma200:.2f}"
                    f"Drop Percentage: {drop_percentage:.2f}%"
                )
                await send_notification(message)
            else:
                print(
                    f"[INFO] EpochTime: {time.time():.2f} {stock} is above 200-day MA or drop percentage is below threshold. No alert sent."
                )
        time.sleep(SLEEP_TIME)  # Wait 60 seconds before checking again


if __name__ == "__main__":
    asyncio.run(monitor_stock())
