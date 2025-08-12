# main.py
import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import ccxt
import mysql.connector
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv
from database import get_connection, create_tables
import openai
import json

load_dotenv()

# إعداد المتغيرات
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
OWNER_WALLET = os.getenv("OWNER_WALLET_ADDRESS", "غير معرف")
openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=5)

# حالات الإدخال
STATE_NONE = 0
STATE_SET_BINANCE_API = 1
STATE_SET_BINANCE_SECRET = 2
STATE_SET_KUCOIN_API = 3
STATE_SET_KUCOIN_SECRET = 4
STATE_SET_KUCOIN_PASS = 5
STATE_SET_INVEST_AMOUNT = 6
STATE_REPORT_START_DATE = 7
STATE_REPORT_END_DATE = 8

user_states = {}

# ----------------------------------------
# مساعدة تشغيل دوال blocking بداخل asyncio
async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))


# ----------------------------------------
# دوال DB (باختصار، يمكنك تعديلها حسب الحاجة)

def set_user_field(user_id, field, value):
    conn = get_connection()
    cursor = conn.cursor()
    # التحقق هل المستخدم موجود
    cursor.execute("SELECT telegram_id FROM users WHERE telegram_id=%s", (user_id,))
    if cursor.fetchone():
        cursor.execute(f"UPDATE users SET {field}=%s WHERE telegram_id=%s", (value, user_id))
    else:
        cursor.execute(
            "INSERT INTO users (telegram_id, {}) VALUES (%s, %s)".format(field),
            (user_id, value)
        )
    conn.commit()
    cursor.close()
    conn.close()


def get_user_field(user_id, field):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT {field} FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return row[0]
    return None


def get_user_active_platforms(user_id):
    platforms = get_user_field(user_id, "active_platforms")
    if platforms:
        try:
            return json.loads(platforms)
        except:
            return []
    return []


def set_user_active_platforms(user_id, platforms):
    platforms_json = json.dumps(platforms)
    set_user_field(user_id, "active_platforms", platforms_json)


def get_invested_amount(user_id):
    val = get_user_field(user_id, "invested_amount")
    if val:
        return float(val)
    return 0.0


def get_profit(user_id):
    val = get_user_field(user_id, "profit")
    if val:
        return float(val)
    return 0.0


def set_profit(user_id, value):
    set_user_field(user_id, "profit", float(value))


def get_bot_profit_percent():
    val = get_user_field("bot", "bot_profit_percent")
    if val:
        return float(val)
    return 5.0  # الافتراضي 5%


def set_bot_profit_percent(value):
    set_user_field("bot", "bot_profit_percent", float(value))


# ----------------------------------------
# التحقق من صلاحية مفاتيح API للمنصات (binance, kucoin)
async def validate_binance_api(api_key, secret):
    try:
        binance = ccxt.binance({"apiKey": api_key, "secret": secret, "enableRateLimit": True})
        balance = await run_in_executor(binance.fetch_balance)
        return True
    except Exception as e:
        logger.warning(f"Binance API validation failed: {e}")
        return False


async def validate_kucoin_api(api_key, secret, password):
    try:
        kucoin = ccxt.kucoin(
            {
                "apiKey": api_key,
                "secret": secret,
                "password": password,
                "enableRateLimit": True,
            }
        )
        balance = await run_in_executor(kucoin.fetch_balance)
        return True
    except Exception as e:
        logger.warning(f"KuCoin API validation failed: {e}")
        return False


async def validate_user_api_keys(user_id):
    binance_api = get_user_field(user_id, "binance_api_key")
    binance_secret = get_user_field(user_id, "binance_secret_key")
    kucoin_api = get_user_field(user_id, "kucoin_api_key")
    kucoin_secret = get_user_field(user_id, "kucoin_secret_key")
    kucoin_pass = get_user_field(user_id, "kucoin_password")

    if binance_api and binance_secret:
        valid_binance = await validate_binance_api(binance_api, binance_secret)
        if not valid_binance:
            return False, "Binance API غير صحيحة أو لا تعمل."
    if kucoin_api and kucoin_secret and kucoin_pass:
        valid_kucoin = await validate_kucoin_api(kucoin_api, kucoin_secret, kucoin_pass)
        if not valid_kucoin:
            return False, "KuCoin API غير صحيحة أو لا تعمل."
    return True, ""


# ----------------------------------------
# القوائم الرئيسية للمستخدم

def get_main_menu_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("1️⃣ تسجيل أو تعديل بيانات التداول", callback_data="menu_edit_trading")],
        [InlineKeyboardButton("2️⃣ بدء استثمار", callback_data="menu_start_invest")],
        [InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data="menu_fake_invest")],
        [InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="menu_report")],
        [InlineKeyboardButton("5️⃣ حالة السوق", callback_data="menu_market_status")],
        [InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest")],
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🔧 قائمة المدير", callback_data="menu_admin")])
    return InlineKeyboardMarkup(keyboard)


def get_back_to_main_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("◀️ رجوع للقائمة الرئيسية", callback_data="menu_main")]]
    )


# ----------------------------------------
# بدء التعامل مع التفاعل


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_states[user_id] = STATE_NONE
    await update.message.reply_text(
        f"مرحبًا بك في بوت الاستثمار الآلي!\n\nمحفظة المالك (الأرباح ستذهب إليها): {OWNER_WALLET}\n"
        "اختر من القائمة أدناه:",
        reply_markup=get_main_menu_keyboard(user_id),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    data = query.data

    if data == "menu_main":
        user_states[user_id] = STATE_NONE
        await query.message.edit_text("القائمة الرئيسية:", reply_markup=get_main_menu_keyboard(user_id))

    elif data == "menu_edit_trading":
        user_states[user_id] = STATE_SET_BINANCE_API
        await query.message.edit_text(
            "أدخل Binance API Key:\n\n"
            "إذا لم يكن لديك، يمكن الحصول عليه من حسابك في Binance.\n"
            "تأكد من تفعيل صلاحيات التداول والقراءة.",
            reply_markup=get_back_to_main_keyboard(),
        )

    elif data == "menu_start_invest":
        # هنا يتم تنفيذ خوارزمية التداول الحقيقي (سأشرح بعدها)
        await query.message.edit_text("جارٍ بدء استثمارك الحقيقي... (قيد التطوير)", reply_markup=get_back_to_main_keyboard())

    elif data == "menu_fake_invest":
        # بدء الاستثمار الوهمي بناء على بيانات يوم سابق
        await start_fake_invest(query, user_id)

    elif data == "menu_report":
        user_states[user_id] = STATE_REPORT_START_DATE
        await query.message.edit_text(
            "أدخل تاريخ بداية الفترة بصيغة YYYY-MM-DD", reply_markup=get_back_to_main_keyboard()
        )

    elif data == "menu_market_status":
        await show_market_status(query, user_id)

    elif data == "menu_stop_invest":
        await query.message.edit_text(
            "تم إيقاف استثمارك. لن يتم استخدام أموالك في التداول حتى تفعّل الاستثمار مرة أخرى.",
            reply_markup=get_back_to_main_keyboard(),
        )
        set_user_field(user_id, "invest_active", "false")

    elif data == "menu_admin" and user_id == ADMIN_ID:
        await query.message.edit_text("قائمة المدير:", reply_markup=get_admin_menu())

    elif data.startswith("admin_") and user_id == ADMIN_ID:
        await handle_admin_actions(query, data)

    else:
        await query.message.reply_text("خيار غير معروف، الرجاء المحاولة مرة أخرى.", reply_markup=get_main_menu_keyboard(user_id))


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id, STATE_NONE)

    if state == STATE_SET_BINANCE_API:
        set_user_field(user_id, "binance_api_key", text)
        user_states[user_id] = STATE_SET_BINANCE_SECRET
        await update.message.reply_text(
            "أدخل Binance Secret Key:",
            reply_markup=get_back_to_main_keyboard(),
        )
    elif state == STATE_SET_BINANCE_SECRET:
        set_user_field(user_id, "binance_secret_key", text)
        user_states[user_id] = STATE_SET_KUCOIN_API
        await update.message.reply_text(
            "أدخل KuCoin API Key:\n\n"
            "للحصول عليه: https://docs.kucoin.com/\n"
            "تأكد من تفعيل صلاحيات التداول والقراءة.",
            reply_markup=get_back_to_main_keyboard(),
        )
    elif state == STATE_SET_KUCOIN_API:
        set_user_field(user_id, "kucoin_api_key", text)
        user_states[user_id] = STATE_SET_KUCOIN_SECRET
        await update.message.reply_text(
            "أدخل KuCoin Secret Key:",
            reply_markup=get_back_to_main_keyboard(),
        )
    elif state == STATE_SET_KUCOIN_SECRET:
        set_user_field(user_id, "kucoin_secret_key", text)
        user_states[user_id] = STATE_SET_KUCOIN_PASS
        await update.message.reply_text(
            "أدخل KuCoin API Password (Passphrase):",
            reply_markup=get_back_to_main_keyboard(),
        )
    elif state == STATE_SET_KUCOIN_PASS:
        set_user_field(user_id, "kucoin_password", text)
        user_states[user_id] = STATE_NONE
        valid, msg = await validate_user_api_keys(user_id)
        if valid:
            await update.message.reply_text(
                "✅ تم التحقق من مفاتيح API بنجاح!",
                reply_markup=get_main_menu_keyboard(user_id),
            )
        else:
            await update.message.reply_text(
                f"❌ خطأ في مفاتيح API: {msg}\n\n"
                "تأكد من إدخال البيانات بشكل صحيح وتفعيل صلاحيات التداول والقراءة.",
                reply_markup=get_main_menu_keyboard(user_id),
            )

    elif state == STATE_SET_INVEST_AMOUNT:
        try:
            amount = float(text)
            if amount <= 0:
                raise ValueError
            # نتحقق إن رصيد المحفظة يسمح بالاستثمار (يمكن إضافة تحقق حقيقي)
            set_user_field(user_id, "invested_amount", amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(
                f"تم تعيين المبلغ المستثمر: {amount} دولار.",
                reply_markup=get_main_menu_keyboard(user_id),
            )
        except:
            await update.message.reply_text(
                "الرجاء إدخال مبلغ صالح أكبر من صفر.",
                reply_markup=get_back_to_main_keyboard(),
            )

    elif state == STATE_REPORT_START_DATE:
        try:
            datetime.strptime(text, "%Y-%m-%d")
            set_user_field(user_id, "report_start_date", text)
            user_states[user_id] = STATE_REPORT_END_DATE
            await update.message.reply_text(
                "أدخل تاريخ نهاية الفترة بصيغة YYYY-MM-DD",
                reply_markup=get_back_to_main_keyboard(),
            )
        except:
            await update.message.reply_text(
                "صيغة التاريخ غير صحيحة. الرجاء استخدام YYYY-MM-DD.",
                reply_markup=get_back_to_main_keyboard(),
            )

    elif state == STATE_REPORT_END_DATE:
        try:
            start_date = get_user_field(user_id, "report_start_date")
            end_date = text
            # تحقق من صحة التاريخ
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            ed = datetime.strptime(end_date, "%Y-%m-%d")
            if ed < sd:
                raise ValueError
            user_states[user_id] = STATE_NONE
            # هنا استدعاء كشف الحساب حسب الفترة (نموذج)
            await send_report(update, user_id, sd, ed)
        except:
            await update.message.reply_text(
                "تاريخ النهاية غير صالح أو أصغر من بداية الفترة.",
                reply_markup=get_back_to_main_keyboard(),
            )

    else:
        await update.message.reply_text(
            "الرجاء اختيار أمر من القائمة أو كتابة الأمر الصحيح.",
            reply_markup=get_main_menu_keyboard(user_id),
        )


# ----------------------------------------
# وظائف إضافية

async def send_report(update, user_id, start_date, end_date):
    # مثال على تقرير مبسط
    profit = get_profit(user_id)
    invested = get_invested_amount(user_id)
    await update.message.reply_text(
        f"كشف الحساب من {start_date.date()} إلى {end_date.date()}:\n"
        f"المبلغ المستثمر: {invested} دولار\n"
        f"الأرباح الحالية: {profit} دولار (تقريبي)\n"
        f"(تقارير تفصيلية قيد التطوير)",
        reply_markup=get_main_menu_keyboard(user_id),
    )


async def start_fake_invest(query, user_id):
    await query.message.edit_text("جارٍ بدء الاستثمار الوهمي بناءً على بيانات يوم سابق...")

    # مثال: نجلب بيانات سعر BTC/USD ليوم سابق (بسيط)
    try:
        binance = ccxt.binance()
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        # نأخذ سعر افتتاح البار الأول ليوم أمس
        ohlcv = await run_in_executor(
            binance.fetch_ohlcv, "BTC/USDT", timeframe="1d", since=None, limit=2
        )
        # ohlcv = [timestamp, open, high, low, close, volume]
        if len(ohlcv) < 2:
            await query.message.reply_text("تعذر الحصول على بيانات السوق ليوم أمس.")
            return
        yesterday_open_price = ohlcv[-2][1]
        await query.message.reply_text(
            f"سعر افتتاح BTC/USDT ليوم أمس: {yesterday_open_price}$\n"
            "ستتم محاكاة عمليات تداول وهمية بناءً على هذا السعر.\n"
            "(التداول الوهمي قيد التطوير)"
        )
    except Exception as e:
        logger.error(f"خطأ في جلب بيانات السوق الوهمي: {e}")
        await query.message.reply_text("خطأ في جلب بيانات السوق الوهمي.")

    await query.message.edit_reply_markup(reply_markup=get_main_menu_keyboard(user_id))


async def show_market_status(query, user_id):
    await query.message.edit_text("جارٍ جلب وتحليل حالة السوق اللحظية...")

    # مثال: جلب سعر BTC/USDT اللحظي
    try:
        binance = ccxt.binance()
        ticker = await run_in_executor(binance.fetch_ticker, "BTC/USDT")
        last_price = ticker["last"]
    except Exception as e:
        logger.error(f"خطأ في جلب سعر السوق: {e}")
        await query.message.edit_text("تعذر الحصول على بيانات السوق اللحظية.")
        return

    # استدعاء openai لتحليل السوق
    prompt = (
        f"سعر البيتكوين الحالي هو {last_price} دولار.\n"
        "اعطني تحليل موجز للسوق ونصائح تداول عملية للمستثمر.\n"
        "اكتب بالعربية الفصحى."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        analysis = response["choices"][0]["message"]["content"]
    except Exception as e:
        logger