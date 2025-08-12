import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import ccxt
from database import get_connection, create_tables
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for tracking user input
STATE_NONE = 0
STATE_BINANCE_API = 1
STATE_BINANCE_SECRET = 2
STATE_KUCOIN_API = 3
STATE_KUCOIN_SECRET = 4
STATE_INVEST_AMOUNT = 5

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("إعداد مفاتيح API", callback_data='set_api')],
        [InlineKeyboardButton("تعيين المبلغ المستثمر", callback_data='set_amount')],
        [InlineKeyboardButton("عرض الأرباح", callback_data='show_profit')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'set_api':
        user_states[user_id] = STATE_BINANCE_API
        await query.message.reply_text("الرجاء إدخال Binance API Key:")
    elif query.data == 'set_amount':
        user_states[user_id] = STATE_INVEST_AMOUNT
        await query.message.reply_text("الرجاء إدخال المبلغ المستثمر (رقم فقط):")
    elif query.data == 'show_profit':
        profit = get_user_profit(user_id)
        await query.message.reply_text(f"الأرباح الحالية: {profit} دولار (تقريبي)")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    state = user_states.get(user_id, STATE_NONE)

    if state == STATE_BINANCE_API:
        set_user_binance_api(user_id, api_key=text)
        user_states[user_id] = STATE_BINANCE_SECRET
        await update.message.reply_text("الرجاء إدخال Binance Secret Key:")
    elif state == STATE_BINANCE_SECRET:
        set_user_binance_secret(user_id, secret_key=text)
        user_states[user_id] = STATE_KUCOIN_API
        await update.message.reply_text("الرجاء إدخال KuCoin API Key:")
    elif state == STATE_KUCOIN_API:
        set_user_kucoin_api(user_id, api_key=text)
        user_states[user_id] = STATE_KUCOIN_SECRET
        await update.message.reply_text("الرجاء إدخال KuCoin Secret Key:")
    elif state == STATE_KUCOIN_SECRET:
        set_user_kucoin_secret(user_id, secret_key=text)
        user_states[user_id] = STATE_NONE
        valid = await validate_api_keys(user_id)
        if valid:
            await update.message.reply_text("تم التحقق من مفاتيح API بنجاح!")
        else:
            await update.message.reply_text("خطأ في مفاتيح API، الرجاء إعادة المحاولة.")
    elif state == STATE_INVEST_AMOUNT:
        if text.replace('.', '', 1).isdigit():
            amount = float(text)
            set_user_invest_amount(user_id, amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(f"تم تعيين المبلغ المستثمر: {amount} دولار")
        else:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")

def set_user_binance_api(user_id, api_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (telegram_id, binance_api_key) VALUES (%s, %s) ON DUPLICATE KEY UPDATE binance_api_key=%s", (user_id, api_key, api_key))
    conn.commit()
    cursor.close()
    conn.close()

def set_user_binance_secret(user_id, secret_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET binance_secret_key=%s WHERE telegram_id=%s", (secret_key, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def set_user_kucoin_api(user_id, api_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET kucoin_api_key=%s WHERE telegram_id=%s", (api_key, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def set_user_kucoin_secret(user_id, secret_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET kucoin_secret_key=%s WHERE telegram_id=%s", (secret_key, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def set_user_invest_amount(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET invested_amount=%s WHERE telegram_id=%s", (amount, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_profit(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT profit FROM users WHERE telegram_id=%s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else 0

async def validate_api_keys(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT binance_api_key, binance_secret_key, kucoin_api_key, kucoin_secret_key FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return False

    binance_api, binance_secret, kucoin_api, kucoin_secret = row

    # تحقق بسيط من Binance API
    try:
        binance = ccxt.binance({
            'apiKey': binance_api,
            'secret': binance_secret,
            'enableRateLimit': True,
        })
        balance = await run_in_executor(binance.fetch_balance)
        # لو جاب بيانات، المفاتيح صالحة
    except Exception as e:
        print(f"Binance API Error: {e}")
        return False

    # تحقق بسيط من KuCoin API
    try:
        kucoin = ccxt.kucoin({
            'apiKey': kucoin_api,
            'secret': kucoin_secret,
            'enableRateLimit': True,
        })
        balance = await run_in_executor(kucoin.fetch_balance)
    except Exception as e:
        print(f"KuCoin API Error: {e}")
        return False

    return True

import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=5)

async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))

def main():
    create_tables()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()