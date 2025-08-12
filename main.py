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
    await update.message.reply_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "manage_trading":
        await manage_trading_menu(query, user_id)
    elif query.data == "start_invest":
        user_states[user_id] = STATE_START_INVEST
        await query.message.reply_text("جاري بدء الاستثمار الحقيقي...")
        # هنا تستدعي الخوارزمية الحقيقية للتداول
        await start_real_investment(user_id, query)
    elif query.data == "virtual_invest":
        user_states[user_id] = STATE_START_VIRTUAL_INVEST
        await query.message.reply_text("جاري بدء الاستثمار الوهمي (على بيانات يوم سابق)...")
        # تستدعي الخوارزمية الوهمية للتداول
        await start_virtual_investment(user_id, query)
    elif query.data == "account_statement":
        # طلب بداية الفترة - هنا مثال على طلب نصي، ممكن تطور تقويم فيما بعد
        user_states[user_id] = STATE_MARKET_ANALYSIS
        await query.message.reply_text("أرسل بداية الفترة (YYYY-MM-DD):")
    elif query.data == "market_status":
        await send_market_analysis(user_id, query)
    elif query.data == "stop_invest":
        # إيقاف الاستثمار
        await stop_user_investment(user_id, query)
    elif query.data == "main_menu":
        await start(query, context)
    else:
        await query.message.reply_text("أمر غير معروف، الرجاء اختيار من القائمة.")


async def manage_trading_menu(query, user_id):
    # تحقق ما إذا كانت المنصات معرفة مسبقًا
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
    # مثال لخوارزمية استثمار حقيقي مبسطة - تحتاج تطوير خوارزميات فعلية
    await query.message.reply_text("تشغيل خوارزمية التداول الحقيقي... (مفعل فقط إذا كانت مفاتيح API صحيحة).")
    # تحقق من المفاتيح ثم نفذ التداول
    valid = await validate_api_keys(user_id)
    if not valid:
        await query.message.reply_text("مفاتيح API غير صحيحة أو غير مكتملة. يرجى التحقق أولاً.")
        return
    # هنا نفذ أوامر شراء وبيع فورية حسب الخوارزمية (مثال فقط)
    await query.message.reply_text("تم تنفيذ أوامر المراجحة الفورية (تحتاج تطبيق فعلي).")


async def start_virtual_investment(user_id, query):
    # مثال لخوارزمية استثمار وهمي بدون أموال حقيقية على بيانات يوم سابق
    await query.message.reply_text("تشغيل خوارزمية الاستثمار الوهمي على بيانات تاريخية ليوم سابق...")
    # استدعاء بيانات اليوم السابق من قاعدة البيانات
    # تنفيذ الحسابات واظهار النتائج الوهمية
    await query.message.reply_text("تم عرض نتائج الاستثمار الوهمي (مثال فقط).")


async def send_market_analysis(user_id, query):
    # مثال لاستدعاء openai لتحليل السوق وتقديم نصائح تداول
    await query.message.reply_text("جاري تحليل السوق باستخدام OpenAI...")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "أنت مساعد خبير في تحليل سوق العملات الرقمية وتعطي نصائح تداول مفيدة."
                },
                {
                    "role": "user",
                    "content": "قدم لي تحليل لحالة السوق الحالية ونصائح استثمارية."
                },
            ],
            max_tokens=250,
            temperature=0.7,
        )
        analysis = response.choices[0].message.content
        await query.message.reply_text(analysis)
    except Exception as e:
        await query.message.reply_text(f"حدث خطأ أثناء تحليل السوق: {e}")


async def stop_user_investment(user_id, query):
    # وضع علامة على أن المستخدم أوقف الاستثمار
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
    elif state == STATE_INVEST_AMOUNT:
        if text.replace(".", "", 1).isdigit():
            amount = float(text)
            set_user_invest_amount(user_id, amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(f"تم تعيين المبلغ المستثمر: {amount} دولار")
        else:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
    elif state == STATE_MARKET_ANALYSIS:
        # مثال: استدعاء كشف حساب الفترة من الرسالة النصية مباشرة
        start_date = text
        statement = get_account_statement(user_id, start_date)
        await update.message.reply_text(statement)
        user_states[user_id] = STATE_NONE
    else:
        await update.message.reply_text("الرجاء اختيار خيار من القائمة أو استخدم /start للعودة للقائمة الرئيسية.")


# الدوال المتعلقة بقاعدة البيانات (أمثلة)

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


def get_user_profit(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT profit FROM users WHERE telegram_id=%s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else 0


def set_user_investment_active(user_id, active: bool):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET investment_active=%s WHERE telegram_id=%s", (active, user_id))
    conn.commit()
    cursor.close()
    conn.close()


def get_account_statement(user_id, start_date):
    # مثال: استعلام الربح حسب التاريخ - تحتاج تعديل لقاعدة بياناتك
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(profit) FROM trades WHERE telegram_id=%s AND trade_date >= %s",
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
        binance = ccxt.binance(
            {
                "apiKey": binance_api,
                "secret": binance_secret,
                "enableRateLimit": True,
            }
        )
        await run_in_executor(binance.fetch_balance)
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
