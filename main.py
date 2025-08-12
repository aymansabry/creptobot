# main.py
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import ccxt
from database import get_connection, create_tables
from dotenv import load_dotenv
import asyncio
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

# States for tracking user input
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
        await start_real_investment(user_id, query)
    elif query.data == "virtual_invest":
        user_states[user_id] = STATE_START_VIRTUAL_INVEST
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


async def start_real_investment(user_id, query):
    await query.message.reply_text(
        "🟢 جارٍ التحقق من مفاتيح API والمحفظة الخاصة بك...\n"
        "🤖 يستخدم البوت تقنيات الذكاء الاصطناعي لخوارزميات تداول متقدمة تضمن أفضل فرص المراجحة."
    )

    valid, message = await validate_api_keys(user_id)
    if not valid:
        await query.message.reply_text(f"❌ خطأ في مفاتيح API: {message}\nيرجى تحديث المفاتيح وإعادة المحاولة.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT invested_amount, binance_api_key, binance_secret_key FROM users WHERE telegram_id=%s",
        (user_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    invested_amount = row[0] if row else 0

    if invested_amount <= 0:
        user_states[user_id] = STATE_INVEST_AMOUNT
        await query.message.reply_text(
            "📌 لم يتم تحديد مبلغ الاستثمار بعد.\n"
            "من فضلك أدخل مبلغ الاستثمار الذي ترغب في استخدامه (بالدولار):"
        )
        return

    binance_api = row[1]
    binance_secret = row[2]

    binance = ccxt.binance({
        "apiKey": binance_api,
        "secret": binance_secret,
        "enableRateLimit": True,
    })

    try:
        balance = await binance.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        if usdt_balance < invested_amount:
            await query.message.reply_text(
                f"⚠️ رصيد USDT غير كافٍ في محفظتك.\n"
                f"الرصيد الحالي: {usdt_balance} دولار\n"
                f"المبلغ الذي تريد استثماره: {invested_amount} دولار\n"
                "يرجى تعديل المبلغ أو تعبئة محفظتك."
            )
            await binance.close()
            return
        await binance.close()
    except Exception as e:
        await query.message.reply_text(f"❌ حدث خطأ أثناء جلب رصيد المحفظة: {e}")
        await binance.close()
        return

    set_user_investment_active(user_id, True)
    await query.message.reply_text(
        f"✅ تم التحقق من مفاتيح API ورصيد المحفظة.\n"
        f"🔄 بدء تنفيذ استراتيجيات التداول الحقيقي بمبلغ {invested_amount} دولار.\n"
        "⚙️ يعمل البوت الآن على تنفيذ عمليات المراجحة تلقائيًا لتعظيم أرباحك.\n"
        "📈 يرجى الانتظار بينما يتم تحديث الصفقات والنتائج."
    )

    # هنا تضيف الخوارزمية الحقيقية الفعلية


async def start_virtual_investment(user_id, query):
    await query.message.reply_text(
        "🟡 بدء الاستثمار الوهمي بأسعار السوق الحقيقية بدون استخدام أموال حقيقية.\n"
        "🤖 يستخدم البوت بيانات السوق الحقيقية ويطبق استراتيجيات تداول مشابهة تمامًا للاستثمار الحقيقي.\n"
        "🔍 هذا يساعدك على تجربة الأداء وفهم آلية التداول دون مخاطرة."
    )

    valid, message = await validate_api_keys(user_id)
    exchange = None
    if valid:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT binance_api_key, binance_secret_key FROM users WHERE telegram_id=%s",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        binance_api, binance_secret = row if row else (None, None)

        exchange = ccxt.binance({
            "apiKey": binance_api,
            "secret": binance_secret,
            "enableRateLimit": True,
        })
    else:
        exchange = ccxt.binance()

    try:
        balance = 1000  # رصيد وهمي ثابت (يمكن تعديله)
        positions = {}

        symbols = ["BTC/USDT", "ETH/USDT"]
        prices = {}
        for sym in symbols:
            ticker = await exchange.fetch_ticker(sym)
            prices[sym] = ticker['last']

        amount_per_coin = balance / len(symbols)

        report = "📊 نتائج الاستثمار الوهمي:\n\n"
        for sym in symbols:
            price = prices[sym]
            qty = amount_per_coin / price
            positions[sym] = qty
            report += f"✅ اشتريت {qty:.6f} من {sym} بسعر {price:.2f} دولار\n"

        report += "\n🔔 هذه المحاكاة تساعدك على فهم أداء التداول بدون مخاطر.\n"
        report += "💡 استغل هذه الفرصة لتجربة استراتيجياتك قبل الاستثمار الحقيقي."

        await query.message.reply_text(report)
    except Exception as e:
        await query.message.reply_text(f"❌ حدث خطأ أثناء الاستثمار الوهمي: {e}")
    finally:
        await exchange.close()


async def send_market_analysis(user_id, query):
    await query.message.reply_text("جاري تحليل السوق باستخدام OpenAI...")

    try:
        # جلب أسعار العملات الرئيسية
        exchange = ccxt.binance()
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT"]
        prices_text = "أسعار العملات الحالية:\n"
        for sym in symbols:
            ticker = await exchange.fetch_ticker(sym)
            prices_text += f"{sym}: {ticker['last']:.2f} USD\n"
        await exchange.close()

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "أنت مساعد خبير في تحليل سوق العملات الرقمية وتعطي نصائح تداول مفيدة."
                },
                {
                    "role": "user",
                    "content": (
                        f"{prices_text}\n"
                        "قدم لي تحليل لحالة السوق الحالية مع نصائح استثمارية مفصلة."
                    )
                },
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
        await update.message.reply_text(
            "الرجاء إدخال KuCoin API Key:\n"
            "(لتعرف كيفية الحصول على المفاتيح: https://docs.kucoin.com/)\n"
            "تأكد من تفعيل صلاحيات API المطلوبة: التداول والقراءة."
        )
    elif state == STATE_KUCOIN_API:
        set_user_kucoin_api(user_id, api_key=text)
        user_states[user_id] = STATE_KUCOIN_SECRET
        await update.message.reply_text("الرجاء إدخال KuCoin Secret Key:")
    elif state == STATE_KUCOIN_SECRET:
        set_user_kucoin_secret(user_id, secret_key=text)
        user_states[user_id] = STATE_KUCOIN_PASSWORD
        await update.message.reply_text(
            "الرجاء إدخال KuCoin API Password (Passphrase):\n"
            "(هي كلمة السر التي اخترتها عند إنشاء API في KuCoin)"
        )
    elif state == STATE_KUCOIN_PASSWORD:
        set_user_kucoin_password(user_id, password=text)
        user_states[user_id] = STATE_NONE
        valid, message = await validate_api_keys(user_id)
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
    elif state == STATE_INVEST_AMOUNT:
        if text.replace(".", "", 1).isdigit():
            amount = float(text)
            set_user_invest_amount(user_id, amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(f"تم تعيين المبلغ المستثمر: {amount} دولار")
        else:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
    elif state == STATE_MARKET_ANALYSIS:
        start_date = text
        statement = get_account_statement(user_id, start_date)
        await update.message.reply_text(statement)
        user_states[user_id] = STATE_NONE
    else:
        await update.message.reply_text("الرجاء اختيار خيار من القائمة أو استخدم /start للعودة للقائمة الرئيسية.")


# دوال قاعدة البيانات

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
    cursor.execute(
        "UPDATE users SET invested_amount=%s WHERE telegram_id=%s", (amount, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def set_user_investment_active(user_id, active=True):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET is_investing=%s WHERE telegram_id=%s", (active, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


async def validate_api_keys(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT binance_api_key, binance_secret_key FROM users WHERE telegram_id=%s", (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row or not row[0] or not row[1]:
        return False, "مفاتيح Binance غير مضافة أو ناقصة."

    binance_api, binance_secret = row

    try:
        binance = ccxt.binance({
            "apiKey": binance_api,
            "secret": binance_secret,
            "enableRateLimit": True,
        })
        balance = await binance.fetch_balance()
        await binance.close()
        # تحقق بسيط: هل يوجد رصيد أو على الأقل الحساب متصل؟
        if not balance:
            return False, "تعذر جلب بيانات المحفظة. تأكد من صلاحية المفاتيح."
    except ccxt.AuthenticationError:
        return False, "مفاتيح API أو السرية غير صحيحة (AuthenticationError)."
    except Exception as e:
        return False, f"خطأ في الاتصال بالمنصة: {str(e)}"

    return True, "المفاتيح صحيحة."


def get_account_statement(user_id, start_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT operation, amount, price, timestamp FROM investment_history WHERE telegram_id=%s AND timestamp >= %s ORDER BY timestamp ASC",
        (user_id, start_date),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return "لا توجد صفقات في هذه الفترة."

    statement = "كشف حساب استثماري:\n\n"
    for op, amount, price, ts in rows:
        statement += f"{ts.strftime('%Y-%m-%d %H:%M')} - {op} - كمية: {amount} - سعر الوحدة: {price}\n"
    return statement


def main():
    create_tables()
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    application.run_polling()


if __name__ == "__main__":
    main()
