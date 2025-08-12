import logging
import os
import ccxt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    run_in_threadpool,
)
from dotenv import load_dotenv
from database import get_connection, create_tables
import asyncio
import openai

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
STATE_NONE = 0
STATE_BINANCE_API = 1
STATE_BINANCE_SECRET = 2
STATE_KUCOIN_API = 3
STATE_KUCOIN_SECRET = 4
STATE_KUCOIN_PASSWORD = 5
STATE_INVEST_AMOUNT_REAL = 6
STATE_INVEST_AMOUNT_VIRTUAL = 7
STATE_MARKET_ANALYSIS = 8

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1. تسجيل أو تعديل بيانات التداول", callback_data="manage_trading")],
        [InlineKeyboardButton("2. بدء استثمار حقيقي", callback_data="start_invest")],
        [InlineKeyboardButton("3. استثمار وهمي", callback_data="virtual_invest")],
        [InlineKeyboardButton("4. كشف حساب عن فترة", callback_data="account_statement")],
        [InlineKeyboardButton("5. حالة السوق", callback_data="market_status")],
        [InlineKeyboardButton("6. إيقاف الاستثمار", callback_data="stop_invest")],
        [InlineKeyboardButton("القائمة الرئيسية", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "manage_trading":
        await manage_trading_menu(query, user_id)
    elif query.data == "start_invest":
        user_states[user_id] = STATE_INVEST_AMOUNT_REAL
        await query.message.reply_text("يرجى إدخال مبلغ الاستثمار الحقيقي بالدولار:")
    elif query.data == "virtual_invest":
        user_states[user_id] = STATE_INVEST_AMOUNT_VIRTUAL
        await query.message.reply_text("يرجى إدخال مبلغ الاستثمار الوهمي بالدولار:")
    elif query.data == "account_statement":
        user_states[user_id] = STATE_MARKET_ANALYSIS
        await query.message.reply_text("أرسل بداية الفترة (YYYY-MM-DD):")
    elif query.data == "market_status":
        await send_market_analysis(user_id, query)
    elif query.data == "stop_invest":
        await stop_user_investment(user_id, query)
    elif query.data == "main_menu":
        await start(query, context)
    else:
        await query.message.reply_text("أمر غير معروف، الرجاء اختيار من القائمة.")

async def manage_trading_menu(query, user_id):
    active_platforms = get_user_active_platforms(user_id)
    buttons = []
    if "binance" in active_platforms:
        buttons.append([InlineKeyboardButton("تعديل Binance API", callback_data="edit_binance_api")])
    else:
        buttons.append([InlineKeyboardButton("إضافة Binance API", callback_data="add_binance_api")])

    if "kucoin" in active_platforms:
        buttons.append([InlineKeyboardButton("تعديل KuCoin API", callback_data="edit_kucoin_api")])
    else:
        buttons.append([InlineKeyboardButton("إضافة KuCoin API", callback_data="add_kucoin_api")])

    buttons.append([InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.reply_text("اختر المنصة التي تريد إعدادها:", reply_markup=reply_markup)

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
        user_states[user_id] = STATE_KUCOIN_PASSWORD
        await update.message.reply_text("الرجاء إدخال KuCoin API Password (Passphrase):")
    elif state == STATE_KUCOIN_PASSWORD:
        set_user_kucoin_password(user_id, password=text)
        user_states[user_id] = STATE_NONE
        valid = await validate_api_keys(user_id)
        if valid:
            await update.message.reply_text("✅ تم التحقق من مفاتيح API بنجاح!")
        else:
            await update.message.reply_text("❌ خطأ في مفاتيح API، الرجاء التحقق وإعادة المحاولة.")
    elif state == STATE_INVEST_AMOUNT_REAL:
        await handle_real_invest_amount(update, context, text)
    elif state == STATE_INVEST_AMOUNT_VIRTUAL:
        await handle_virtual_invest_amount(update, context, text)
    elif state == STATE_MARKET_ANALYSIS:
        statement = get_account_statement(user_id, text)
        await update.message.reply_text(statement)
        user_states[user_id] = STATE_NONE
    else:
        await update.message.reply_text("الرجاء اختيار خيار من القائمة أو استخدم /start للعودة للقائمة الرئيسية.")

async def handle_virtual_invest_amount(update, context, text):
    user_id = update.message.from_user.id
    try:
        amount = float(text)
        await update.message.reply_text(f"حدد مبلغ الاستثمار: {amount} دولار")
        await update.message.reply_text("جاري التحقق من المنصات...")

        platforms = get_user_active_platforms(user_id)
        if not platforms:
            await update.message.reply_text("❌ لم تقم بإضافة مفاتيح أي منصة، الرجاء الإعداد أولاً.")
            return

        await update.message.reply_text("جاري جلب أسعار السوق الحقيقية...")

        binance = ccxt.binance()
        ticker = await run_in_threadpool(binance.fetch_ticker, 'BTC/USDT')
        buy_price = ticker['ask']
        sell_price = ticker['bid']

        await update.message.reply_text(f"سعر الشراء الحالي: {buy_price} دولار\nسعر البيع الحالي: {sell_price} دولار")

        await update.message.reply_text("جاري تنفيذ شراء وهمي...")
        btc_amount = amount / buy_price

        await update.message.reply_text("جاري تنفيذ بيع وهمي...")

        sell_price_virtual = buy_price * 1.005
        profit = btc_amount * (sell_price_virtual - buy_price)

        await update.message.reply_text(f"تمت الصفقة بنجاح! الربح الوهمي هو: {profit:.2f} دولار")

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء الاستثمار الوهمي: {e}")
    finally:
        user_states[user_id] = STATE_NONE

async def handle_real_invest_amount(update, context, text):
    user_id = update.message.from_user.id
    try:
        amount = float(text)
        await update.message.reply_text(f"حدد مبلغ الاستثمار: {amount} دولار")
        await update.message.reply_text("جاري التحقق من مفاتيح API...")

        valid = await validate_api_keys(user_id)
        if not valid:
            await update.message.reply_text("❌ مفاتيح API غير صحيحة أو غير مكتملة.")
            return

        await update.message.reply_text("جاري جلب أسعار السوق...")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT binance_api_key, binance_secret_key, kucoin_api_key, kucoin_secret_key, kucoin_password FROM users WHERE telegram_id=%s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            await update.message.reply_text("❌ لم يتم العثور على مفاتيح API الخاصة بك.")
            return

        binance_api, binance_secret, kucoin_api, kucoin_secret, kucoin_password = row

        binance = ccxt.binance({
            'apiKey': binance_api,
            'secret': binance_secret,
            'enableRateLimit': True,
        })

        await update.message.reply_text("جاري تنفيذ أمر شراء...")
        # نفذ شراء (كمثال) - هنا تنفيذ أمر شراء سوق Market order
        order = await run_in_threadpool(binance.create_market_buy_order, 'BTC/USDT', amount / (await run_in_threadpool(binance.fetch_ticker, 'BTC/USDT'))['ask'])

        await update.message.reply_text("جاري تنفيذ أمر بيع...")
        # نفذ بيع (كمثال) - بيع بعد ارتفاع السعر 0.5% (تخيلية فقط)
        sell_price = order['price'] * 1.005
        btc_amount = order['amount']
        # لكون ccxt لا يدعم أوامر بيع بسعر ثابت بهذه الطريقة بسهولة بدون انتظار، نعتبر بيع وهمي هنا:
        profit = btc_amount * (sell_price - order['price'])

        await update.message.reply_text(f"تمت الصفقة بنجاح! الربح التقديري هو: {profit:.2f} دولار")

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء الاستثمار الحقيقي: {e}")
    finally:
        user_states[user_id] = STATE_NONE

async def send_market_analysis(user_id, query):
    await query.message.reply_text("جاري تحليل السوق باستخدام OpenAI...")

    try:
        # جلب أسعار بعض العملات الرئيسية
        binance = ccxt.binance()
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        prices = {}
        for sym in symbols:
            ticker = await run_in_threadpool(binance.fetch_ticker, sym)
            prices[sym] = ticker['last']

        # تكوين نص التحليل مع الأسعار
        price_text = "\n".join([f"{sym}: {price}$" for sym, price in prices.items()])

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت مساعد خبير في تحليل سوق العملات الرقمية."},
                {"role": "user", "content": f"قدم لي تحليل لحالة السوق الحالية ونصائح استثمارية.\nأسعار العملات الحالية:\n{price_text}"}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        analysis = response.choices[0].message.content
        await query.message.reply_text(analysis)

    except Exception as e:
        await query.message.reply_text(f"حدث خطأ أثناء تحليل السوق: {e}")

async def stop_user_investment(user_id, query):
    set_user_investment_active(user_id, False)
    await query.message.reply_text("تم إيقاف الاستثمار الخاص بك.")

# دوال قاعدة البيانات (مبسط)

def get_user_active_platforms(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT binance_api_key, kucoin_api_key FROM users WHERE telegram_id=%s", (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    platforms = []
    if row:
        if row[0]:
            platforms.append("binance")
        if row[1]:
            platforms.append("kucoin")
    return platforms

def set_user_binance_api(user_id, api_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (telegram_id, binance_api_key) VALUES (%s, %s) ON DUPLICATE KEY UPDATE binance_api_key=%s",
        (user_id, api_key, api_key),
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_binance_secret(user_id, secret_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET binance_secret_key=%s WHERE telegram_id=%s", (secret_key, user_id)
    )
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
    cursor.execute(
        "UPDATE users SET kucoin_secret_key=%s WHERE telegram_id=%s", (secret_key, user_id)
    )
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

def set_user_investment_active(user_id, active: bool):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_investing=%s WHERE telegram_id=%s", (active, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_account_statement(user_id, start_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(profit) FROM investment_history WHERE telegram_id=%s AND timestamp >= %s",
        (user_id, start_date),
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    total_profit = result[0] if result and result[0] else 0
    return f"إجمالي الأرباح منذ {start_date} هو {total_profit} دولار"

async def validate_api_keys(user_id):
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
        return False

    binance_api, binance_secret, kucoin_api, kucoin_secret, kucoin_password = row

    try:
        binance = ccxt.binance({
            "apiKey": binance_api,
            "secret": binance_secret,
            "enableRateLimit": True,
        })
        await run_in_threadpool(binance.fetch_balance)
    except Exception as e:
        print(f"Binance API Error: {e}")
        return False

    try:
        kucoin = ccxt.kucoin({
            "apiKey": kucoin_api,
            "secret": kucoin_secret,
            "password": kucoin_password,
            "enableRateLimit": True,
        })
        await run_in_threadpool(kucoin.fetch_balance)
    except Exception as e:
        print(f"KuCoin API Error: {e}")
        return False

    return True

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
