import logging
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
import ccxt
import openai
from database import get_connection, create_tables
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=5)

# User interaction states
STATE_NONE = 0
STATE_BINANCE_API = 1
STATE_BINANCE_SECRET = 2
STATE_KUCOIN_API = 3
STATE_KUCOIN_SECRET = 4
STATE_KUCOIN_PASSWORD = 5
STATE_INVEST_AMOUNT = 6
STATE_SELECT_MENU = 7

user_states = {}
user_menu_context = {}

# --- Utility async wrapper for sync functions ---
async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))

# --- Database functions (assume your database.py provides these or add them here) ---

def set_user_binance_api(user_id, api_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (telegram_id, binance_api_key) VALUES (%s, %s) "
        "ON DUPLICATE KEY UPDATE binance_api_key=%s",
        (user_id, api_key, api_key),
    )
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

def set_user_kucoin_password(user_id, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET kucoin_password=%s WHERE telegram_id=%s", (password, user_id))
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

def get_user_invest_amount(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT invested_amount FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return row[0]
    return 0

def get_user_platform_keys(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT binance_api_key, binance_secret_key, kucoin_api_key, kucoin_secret_key, kucoin_password FROM users WHERE telegram_id=%s",
        (user_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return {}
    return {
        "binance_api_key": row[0],
        "binance_secret_key": row[1],
        "kucoin_api_key": row[2],
        "kucoin_secret_key": row[3],
        "kucoin_password": row[4],
    }

def log_trade(user_id, platform, side, symbol, amount, price):
    # سجّل الصفقة في قاعدة البيانات - أضف جدول trades إذا لم يكن موجوداً
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT,
            platform VARCHAR(50),
            side VARCHAR(10),
            symbol VARCHAR(20),
            amount FLOAT,
            price FLOAT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.execute("""
        INSERT INTO trades (telegram_id, platform, side, symbol, amount, price)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, platform, side, symbol, amount, price))
    conn.commit()
    cursor.close()
    conn.close()

# --- Validation for APIs ---
async def validate_api_keys(user_id):
    keys = get_user_platform_keys(user_id)
    if not keys:
        return False

    # تحقق من Binance
    try:
        if keys["binance_api_key"] and keys["binance_secret_key"]:
            binance = ccxt.binance({
                "apiKey": keys["binance_api_key"],
                "secret": keys["binance_secret_key"],
                "enableRateLimit": True,
            })
            await run_in_executor(binance.fetch_balance)
        else:
            # مفاتيح Binance غير مكتملة
            pass
    except Exception as e:
        logger.warning(f"Binance API error for user {user_id}: {e}")
        return False

    # تحقق من KuCoin
    try:
        if keys["kucoin_api_key"] and keys["kucoin_secret_key"] and keys["kucoin_password"]:
            kucoin = ccxt.kucoin({
                "apiKey": keys["kucoin_api_key"],
                "secret": keys["kucoin_secret_key"],
                "password": keys["kucoin_password"],
                "enableRateLimit": True,
            })
            await run_in_executor(kucoin.fetch_balance)
        else:
            # مفاتيح KuCoin غير مكتملة
            pass
    except Exception as e:
        logger.warning(f"KuCoin API error for user {user_id}: {e}")
        return False

    return True

# --- تحليل السوق عبر OpenAI ---
async def openai_market_analysis(prices_summary: str) -> str:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت خبير في تحليل أسواق العملات الرقمية وتقديم نصائح تداول عملية."},
                {"role": "user", "content": prices_summary},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return f"عذراً، حدث خطأ في تحليل السوق: {str(e)}"

# --- استثمار وهمي (بيانات اليوم) ---
async def simulate_fake_investment(user_id):
    invested_amount = get_user_invest_amount(user_id)
    if invested_amount <= 0:
        return "الرجاء تعيين مبلغ الاستثمار أولاً."

    try:
        exchange = ccxt.binance()
        since = int(datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        ohlcv = await run_in_executor(exchange.fetch_ohlcv, 'BTC/USDT', '1d', since, 1)
        if not ohlcv:
            return "لا توجد بيانات اليوم للاستثمار الوهمي."
        open_price = ohlcv[0][1]
        close_price = ohlcv[0][4]
        btc_amount = invested_amount / open_price
        profit = (close_price - open_price) * btc_amount
        return (f"استثمار وهمي لليوم الحالي:\n"
                f"سعر الافتتاح: {open_price}$\n"
                f"سعر الإغلاق: {close_price}$\n"
                f"كمية BTC المشتراة: {btc_amount:.6f}\n"
                f"الربح/الخسارة المحققة: {profit:.2f}$")
    except Exception as e:
        logger.error(f"simulate_fake_investment error: {e}")
        return f"خطأ في محاكاة الاستثمار الوهمي: {str(e)}"

# --- تنفيذ تداول حقيقي (شراء/بيع) ---
async def execute_real_trade(user_id, side='buy', symbol='BTC/USDT', amount=None):
    keys = get_user_platform_keys(user_id)
    invested_amount = get_user_invest_amount(user_id)
    if invested_amount <= 0:
        return "الرجاء تعيين مبلغ الاستثمار أولاً."

    # اختيار المنصة (مثلاً Binance أولاً إذا متوفر)
    platform_name = None
    exchange = None

    if keys.get("binance_api_key") and keys.get("binance_secret_key"):
        platform_name = "binance"
        exchange = ccxt.binance({
            "apiKey": keys["binance_api_key"],
            "secret": keys["binance_secret_key"],
            "enableRateLimit": True,
        })
    elif keys.get("kucoin_api_key") and keys.get("kucoin_secret_key") and keys.get("kucoin_password"):
        platform_name = "kucoin"
        exchange = ccxt.kucoin({
            "apiKey": keys["kucoin_api_key"],
            "secret": keys["kucoin_secret_key"],
            "password": keys["kucoin_password"],
            "enableRateLimit": True,
        })
    else:
        return "لم تقم بتفعيل أي منصة تداول."

    try:
        await run_in_executor(exchange.load_markets)
        ticker = await run_in_executor(exchange.fetch_ticker, symbol)
        price = ticker['last']

        if amount is None:
            amount = invested_amount / price

        order = await run_in_executor(exchange.create_order, symbol, 'market', side, amount)

        # سجل الصفقة
        log_trade(user_id, platform_name, side, symbol, amount, price)

        return f"✅ تم تنفيذ أمر {side} على {symbol} بكمية {amount:.6f} بسعر {price:.2f}$."
    except Exception as e:
        logger.error(f"execute_real_trade error: {e}")
        return f"❌ خطأ في تنفيذ الصفقة: {str(e)}"

# --- القوائم الرئيسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ تسجيل أو تعديل بيانات التداول", callback_data='menu_setup')],
        [InlineKeyboardButton("2️⃣ ابدأ استثمار حقيقي", callback_data='menu_start_invest')],
        [InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data='menu_fake_invest')],
        [InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data='menu_account_statement')],
        [InlineKeyboardButton("5️⃣ حالة السوق", callback_data='menu_market_status')],
        [InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data='menu_stop_invest')],
        [InlineKeyboardButton("🛑 خروج", callback_data='exit')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)
    user_states[update.effective_user.id] = STATE_SELECT_MENU

# --- العودة للقائمة الرئيسية ---
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# --- التعامل مع الضغط على الأزرار ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    data = query.data

    if data == 'exit':
        await query.message.reply_text("تم إنهاء الجلسة، إلى اللقاء!")
        user_states[user_id] = STATE_NONE
        return

    if data == 'menu_setup':
        user_states[user_id] = STATE_BINANCE_API
        await query.message.reply_text(
            "🔑 الرجاء إدخال Binance API Key:"
        )
        return

    if data == 'menu_start_invest':
        msg = await execute_real_trade(user_id, side='buy')
        await query.message.reply_text(msg)
        await back_to_main_menu(update, context)
        return

    if data == 'menu_fake_invest':
        msg = await simulate_fake_investment(user_id)
        await query.message.reply_text(msg)
        await back_to_main_menu(update, context)
        return

    if data == 'menu_account_statement':
        await query.message.reply_text(
            "📅 من فضلك أرسل تاريخ بداية الفترة بصيغة YYYY-MM-DD:"
        )
        user_states[user_id] = 'awaiting_statement_date'
        return

    if data == 'menu_market_status':
        market_status_msg = await get_market_status_msg()
        await query.message.reply_text(market_status_msg)
        await back_to_main_menu(update, context)
        return

    if data == 'menu_stop_invest':
        # يمكن إضافة تفعيل/تعطيل من قاعدة بيانات لاحقاً
        await query.message.reply_text("✅ تم إيقاف الاستثمار الخاص بك مؤقتًا.")
        await back_to_main_menu(update, context)
        return

    # إضافة أزرار أخرى حسب الحاجة...

# --- استقبال الرسائل النصية ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id, STATE_NONE)

    # معالجة حالة انتظار إدخال Binance API
    if state == STATE_BINANCE_API:
        set_user_binance_api(user_id, text)
        user_states[user_id] = STATE_BINANCE_SECRET
        await update.message.reply_text("🔑 الرجاء إدخال Binance Secret Key:")
        return

    if state == STATE_BINANCE_SECRET:
        set_user_binance_secret(user_id, text)
        user_states[user_id] = STATE_KUCOIN_API
        await update.message.reply_text(
            "🔑 الرجاء إدخال KuCoin API Key:\n"
            "(لتعرف كيفية الحصول على المفاتيح: https://docs.kucoin.com/)\n"
            "تأكد من تفعيل صلاحيات التداول والقراءة."
        )
        return

    if state == STATE_KUCOIN_API:
        set_user_kucoin_api(user_id, text)
        user_states[user_id] = STATE_KUCOIN_SECRET
        await update.message.reply_text("🔑 الرجاء إدخال KuCoin Secret Key:")
        return

    if state == STATE_KUCOIN_SECRET:
        set_user_kucoin_secret(user_id, text)
        user_states[user_id] = STATE_KUCOIN_PASSWORD
        await update.message.reply_text(
            "🔑 الرجاء إدخال KuCoin API Password (Passphrase):\n"
            "(هي كلمة السر التي اخترتها عند إنشاء API في KuCoin)"
        )
        return

    if state == STATE_KUCOIN_PASSWORD:
        set_user_kucoin_password(user_id, text)
        valid = await validate_api_keys(user_id)
        if valid:
            await update.message.reply_text("✅ تم التحقق من مفاتيح API بنجاح!")
        else:
            await update.message.reply_text(
                "❌ خطأ في مفاتيح API، الرجاء التأكد وإعادة المحاولة.\n\n"
                "تأكد من:\n"
                "- إدخال API Key، Secret Key، وPassword بشكل صحيح.\n"
                "- تفعيل صلاحيات التداول والقراءة في حساب KuCoin API.\n"
                "- عدم وجود قيود أمان تمنع الوصول."
            )
        user_states[user_id] = STATE_NONE
        await back_to_main_menu(update, context)
        return

    if state == STATE_INVEST_AMOUNT:
        if text.replace('.', '', 1).isdigit():
            amount = float(text)
            set_user_invest_amount(user_id, amount)
            await update.message.reply_text(f"✅ تم تعيين المبلغ المستثمر: {amount} دولار")
        else:
            await update.message.reply_text("❌ الرجاء إدخال رقم صالح.")
        user_states[user_id] = STATE_NONE
        await back_to_main_menu(update, context)
        return

    if state == 'awaiting_statement_date':
        # هنا يمكن استدعاء دالة استخراج كشف حساب لفترة محددة (غير مدمجة حالياً)
        await update.message.reply_text(f"📄 سيتم عرض كشف الحساب للفترة ابتداءً من: {text}\n(الميزة قيد التطوير حالياً)")
        user_states[user_id] = STATE_NONE
        await back_to_main_menu(update, context)
        return

    # الرد العام أو تعليمات
    await update.message.reply_text("الرجاء استخدام الأزرار للتنقل بين الخيارات.")

# --- تحليل حالة السوق اللحظي مع نصائح باستخدام OpenAI ---
async def get_market_status_msg():
    try:
        exchange = ccxt.binance()
        await run_in_executor(exchange.load_markets)
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        prices = []
        for symbol in symbols:
            ticker = await run_in_executor(exchange.fetch_ticker, symbol)
            prices.append(f"{symbol}: {ticker['last']}$")
        prices_summary = "\n".join(prices)
        analysis = await openai_market_analysis(prices_summary)
        return f"📊 أسعار العملات الرئيسية:\n{prices_summary}\n\n💡 تحليل السوق ونصائح:\n{analysis}"
    except Exception as e:
        logger.error(f"get_market_status_msg error: {e}")
        return f"خطأ في جلب حالة السوق: {str(e)}"

# --- البرنامج الرئيسي ---
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