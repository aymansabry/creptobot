import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import ccxt.async_support as ccxt
from database import get_connection, create_tables
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import openai

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for user input
STATE_NONE = 0
STATE_BINANCE_API = 1
STATE_BINANCE_SECRET = 2
STATE_KUCOIN_API = 3
STATE_KUCOIN_SECRET = 4
STATE_KUCOIN_PASSWORD = 5
STATE_INVEST_AMOUNT = 6
STATE_START_INVEST = 7
STATE_START_VIRTUAL_INVEST = 8
STATE_MARKET_ANALYSIS = 9

user_states = {}
user_virtual_portfolios = {}  # لتخزين محفظة الاستثمار الوهمي لكل مستخدم

executor = ThreadPoolExecutor(max_workers=5)

async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))


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
    if update.message:
        await update.message.reply_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "manage_trading":
        await manage_trading_menu(query, user_id)
    elif query.data == "start_invest":
        user_states[user_id] = STATE_START_INVEST
        await query.message.reply_text("جاري بدء الاستثمار الحقيقي...")
        await start_real_investment(user_id, query)
    elif query.data == "virtual_invest":
        user_states[user_id] = STATE_START_VIRTUAL_INVEST
        await query.message.reply_text("جاري بدء الاستثمار الوهمي (أسعار حقيقية بدون أموال)...")
        await start_virtual_investment(user_id, query)
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


# --- الاستثمار الحقيقي ---

async def start_real_investment(user_id, query):
    valid = await validate_api_keys(user_id)
    if not valid:
        await query.message.reply_text("مفاتيح API غير صحيحة أو غير مكتملة. يرجى التحقق أولاً.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT invested_amount FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row or row[0] <= 0:
        await query.message.reply_text("لم يتم تعيين مبلغ الاستثمار. الرجاء تعيينه أولاً.")
        user_states[user_id] = STATE_INVEST_AMOUNT
        await query.message.reply_text("يرجى إرسال مبلغ الاستثمار بالدولار:")
        return

    invested_amount = row[0]

    await query.message.reply_text(f"بدء استثمار حقيقي بمبلغ {invested_amount} دولار...")

    # مثال تنفيذ أمر شراء BTC/USDT بسعر السوق
    try:
        keys = await get_user_api_keys(user_id)
        binance = ccxt.binance(
            {
                "apiKey": keys['binance_api_key'],
                "secret": keys['binance_secret_key'],
                "enableRateLimit": True,
            }
        )

        balance = await run_in_executor(binance.fetch_balance)
        usdt_balance = balance['free'].get('USDT', 0)
        if usdt_balance < invested_amount:
            await query.message.reply_text(f"رصيد USDT في المحفظة أقل من مبلغ الاستثمار ({usdt_balance} < {invested_amount})")
            await binance.close()
            return

        ticker = await run_in_executor(binance.fetch_ticker, "BTC/USDT")
        price = ticker['last']

        amount_crypto = invested_amount / price

        order = await run_in_executor(binance.create_market_buy_order, "BTC/USDT", amount_crypto)
        await query.message.reply_text(f"تم شراء {amount_crypto:.6f} BTC بسعر {price} دولار.")
        await binance.close()
    except Exception as e:
        await query.message.reply_text(f"خطأ في تنفيذ الصفقة: {e}")


# --- الاستثمار الوهمي ---

class VirtualPortfolio:
    def __init__(self, initial_balance=1000):
        self.balance = initial_balance
        self.crypto_amount = 0
        self.last_price = None

    async def update_price(self, exchange, symbol):
        ticker = await exchange.fetch_ticker(symbol)
        self.last_price = ticker['last']

    def buy(self, amount_usd):
        if self.last_price is None:
            return "السعر غير متاح حالياً"
        if amount_usd > self.balance:
            return "الرصيد غير كافي"
        crypto_bought = amount_usd / self.last_price
        self.crypto_amount += crypto_bought
        self.balance -= amount_usd
        return f"تم شراء {crypto_bought:.6f} وحدة بسعر {self.last_price}"

    def sell(self, amount_crypto):
        if amount_crypto > self.crypto_amount:
            return "الكمية غير كافية للبيع"
        usd_gained = amount_crypto * self.last_price
        self.crypto_amount -= amount_crypto
        self.balance += usd_gained
        return f"تم بيع {amount_crypto:.6f} وحدة بسعر {self.last_price}"

    def get_total_balance(self):
        if self.last_price is None:
            return self.balance
        return self.balance + self.crypto_amount * self.last_price


async def start_virtual_investment(user_id, query):
    exchange = ccxt.binance()
    portfolio = VirtualPortfolio()
    user_virtual_portfolios[user_id] = portfolio

    await portfolio.update_price(exchange, "BTC/USDT")
    buy_msg = portfolio.buy(500)  # شراء وهمي بمبلغ 500 دولار
    await query.message.reply_text(buy_msg)

    await asyncio.sleep(10)  # انتظار 10 ثواني كمثال لتحديث السعر

    await portfolio.update_price(exchange, "BTC/USDT")
    sell_msg = portfolio.sell(0.01)  # بيع وهمي 0.01 BTC
    await query.message.reply_text(sell_msg)

    total = portfolio.get_total_balance()
    await query.message.reply_text(f"الرصيد الكلي الوهمي الآن: {total:.2f} دولار")

    await exchange.close()


# --- حالة السوق وتحليل مع نصائح متقدمة ---

async def send_market_analysis(user_id, query):
    await query.message.reply_text("جاري تحليل السوق باستخدام OpenAI...")

    exchange = ccxt.binance()
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT']
    prices = {}

    try:
        for symbol in symbols:
            ticker = await run_in_executor(exchange.fetch_ticker, symbol)
            prices[symbol] = ticker['last']

        price_report = "\n".join([f"{s}: {p:.2f} دولار" for s, p in prices.items()])

        prompt = (
            "أنت مساعد خبير في تحليل سوق العملات الرقمية.\n"
            f"أسعار العملات الحالية:\n{price_report}\n"
            "قدم لي نصائح استثمارية مفصلة مع تفسيرات مبسطة."
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت مساعد خبير في تحليل سوق العملات الرقمية وتعطي نصائح تداول."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.7,
        )
        analysis = response.choices[0].message.content
        await query.message.reply_text(analysis)

    except Exception as e:
        await query.message.reply_text(f"حدث خطأ أثناء تحليل السوق: {e}")
    finally:
        await exchange.close()


# --- إيقاف الاستثمار ---

async def stop_user_investment(user_id, query):
    set_user_investment_active(user_id, False)
    await query.message.reply_text("تم إيقاف الاستثمار الخاص بك.")


# --- الدوال المساعدة ---

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
        binance = ccxt.binance(
            {
                "apiKey": binance_api,
                "secret": binance_secret,
                "enableRateLimit": True,
            }
        )
        await run_in_executor(binance.fetch_balance)
        await binance.close()
    except Exception as e:
        print(f"Binance API Error: {e}")
        return False

    try:
        kucoin = ccxt.kucoin(
            {
                "apiKey": kucoin_api,
                "secret": kucoin_secret,
                "password": kucoin_password,
                "enableRateLimit": True,
            }
        )
        await run_in_executor(kucoin.fetch_balance)
        await kucoin.close()
    except Exception as e:
        print(f"KuCoin API Error: {e}")
        return False

    return True


async def get_user_api_keys(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT binance_api_key, binance_secret_key FROM users WHERE telegram_id=%s",
        (user_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return {"binance_api_key": None, "binance_secret_key": None}
    return {"binance_api_key": row[0], "binance_secret_key": row[1]}


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


def set_user_invest_amount(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET invested_amount=%s WHERE telegram_id=%s", (amount, user_id))
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
        "SELECT SUM(amount) FROM investment_history WHERE telegram_id=%s AND timestamp >= %s",
        (user_id, start_date),
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    total_profit = result[0] if result and result[0] else 0
    return f"إجمالي الأرباح منذ {start_date} هو {total_profit} دولار"


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id, STATE_NONE)

    if state == STATE_BINANCE_API:
        set_user_binance_api(user_id, api_key=text)
        user_states[user_id] = STATE_BINANCE_SECRET
        await update.message.reply_text("أرسل الآن Binance Secret Key:")
    elif state == STATE_BINANCE_SECRET:
        set_user_binance_secret(user_id, secret_key=text)
        user_states[user_id] = STATE_KUCOIN_API
        await update.message.reply_text("أرسل KuCoin API Key (أو اكتب تخطي إذا لم تستخدم KuCoin):")
    elif state == STATE_KUCOIN_API:
        if text.lower() == "تخطي":
            user_states[user_id] = STATE_INVEST_AMOUNT
            await update.message.reply_text("أرسل مبلغ الاستثمار بالدولار:")
        else:
            set_user_kucoin_api(user_id, api_key=text)
            user_states[user_id] = STATE_KUCOIN_SECRET
            await update.message.reply_text("أرسل KuCoin Secret Key:")
    elif state == STATE_KUCOIN_SECRET:
        set_user_kucoin_secret(user_id, secret_key=text)
        user_states[user_id] = STATE_KUCOIN_PASSWORD
        await update.message.reply_text("أرسل KuCoin Password:")
    elif state == STATE_KUCOIN_PASSWORD:
        set_user_kucoin_password(user_id, password=text)
        user_states[user_id] = STATE_INVEST_AMOUNT
        await update.message.reply_text("أرسل مبلغ الاستثمار بالدولار:")
    elif state == STATE_INVEST_AMOUNT:
        try:
            amount = float(text)
            set_user_invest_amount(user_id, amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(f"تم تعيين مبلغ الاستثمار إلى {amount} دولار.")
        except ValueError:
            await update.message.reply_text("الرجاء إدخال رقم صحيح لمبلغ الاستثمار.")
    elif state == STATE_MARKET_ANALYSIS:
        # افترض أن النص تاريخ البداية
        # إرسال كشف حساب للفترة
        statement = get_account_statement(user_id, text)
        user_states[user_id] = STATE_NONE
        await update.message.reply_text(statement)
    else:
        await update.message.reply_text("يرجى اختيار أمر من القائمة باستخدام /start")


def main():
    create_tables()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
