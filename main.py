import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)
import ccxt
from database import get_connection, create_tables
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for tracking user input
STATE_NONE = 0
STATE_PLATFORM_SELECTION = 10
STATE_API_KEY = 11
STATE_SECRET_KEY = 12
STATE_PASSWORD = 13
STATE_INVEST_AMOUNT = 20

user_states = {}
user_platforms = {}  # to keep track of which platform user is inputting keys for

PLATFORMS = ['Binance', 'KuCoin']

def create_new_user_if_not_exists(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users WHERE telegram_id = %s", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (telegram_id, active_platforms) VALUES (%s, %s)",
            (user_id, json.dumps([]))
        )
        conn.commit()
    cursor.close()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1. تسجيل أو تعديل بيانات التداول", callback_data='trade_data')],
        [InlineKeyboardButton("2. ابدأ استثمار", callback_data='start_invest')],
        [InlineKeyboardButton("3. استثمار وهمي", callback_data='virtual_invest')],
        [InlineKeyboardButton("4. كشف حساب عن فترة", callback_data='account_statement')],
        [InlineKeyboardButton("5. حالة السوق", callback_data='market_status')],
        [InlineKeyboardButton("6. إيقاف الاستثمار", callback_data='stop_invest')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحبًا! اختر من القائمة:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'trade_data':
        # عرض قائمة المنصات لتعديل أو إضافة مفاتيح API
        keyboard = []
        # استعلام المنصات المعرفة للمستخدم
        platforms = get_user_active_platforms(user_id)
        if platforms:
            for p in platforms:
                keyboard.append([InlineKeyboardButton(f"تعديل {p}", callback_data=f"edit_{p.lower()}")])
        # خيار إضافة منصة جديدة فقط إذا أقل من كل المنصات
        if len(platforms) < len(PLATFORMS):
            keyboard.append([InlineKeyboardButton("إضافة منصة جديدة", callback_data="add_platform")])
        keyboard.append([InlineKeyboardButton("العودة للرئيسية", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("اختر المنصة للتعديل أو الإضافة:", reply_markup=reply_markup)

    elif query.data == 'add_platform':
        # عرض المنصات الغير مفعلة حتى يختار منها
        user_active = get_user_active_platforms(user_id)
        available = [p for p in PLATFORMS if p not in user_active]
        keyboard = [[InlineKeyboardButton(p, callback_data=f"platform_{p.lower()}")] for p in available]
        keyboard.append([InlineKeyboardButton("العودة", callback_data="trade_data")])
        await query.message.edit_text("اختر المنصة التي تريد إضافتها:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('platform_'):
        platform = query.data.split('_')[1]
        user_platforms[user_id] = platform
        user_states[user_id] = STATE_API_KEY
        await query.message.edit_text(f"الرجاء إدخال API Key لمنصة {platform.capitalize()}:")

    elif query.data.startswith('edit_'):
        platform = query.data.split('_')[1]
        user_platforms[user_id] = platform
        user_states[user_id] = STATE_API_KEY
        await query.message.edit_text(f"تعديل مفاتيح منصة {platform.capitalize()}. الرجاء إدخال API Key:")

    elif query.data == 'main_menu':
        await start(update, context)

    elif query.data == 'start_invest':
        # ابدأ استثمار بناء على معلومات المستخدم السابقة
        await query.message.reply_text("بدأ الاستثمار باستخدام المعلومات المسجلة لديك... (قيد التطوير)")

    elif query.data == 'virtual_invest':
        await query.message.reply_text("عرض استثمار وهمي بدون استخدام أموال حقيقية... (قيد التطوير)")

    elif query.data == 'account_statement':
        await query.message.reply_text("الرجاء إدخال بداية الفترة (yyyy-mm-dd) لاستدعاء كشف الحساب... (قيد التطوير)")

    elif query.data == 'market_status':
        await query.message.reply_text("تحليل حالة السوق ونصائح الاستثمار... (قيد التطوير)")

    elif query.data == 'stop_invest':
        await query.message.reply_text("تم إيقاف الاستثمار حسب طلبك. لن يتم استخدام أموالك حتى تقوم بالتفعيل مجددًا.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id, STATE_NONE)
    platform = user_platforms.get(user_id)

    if state == STATE_API_KEY:
        save_api_key(user_id, platform, text)
        user_states[user_id] = STATE_SECRET_KEY
        await update.message.reply_text(f"الرجاء إدخال Secret Key لمنصة {platform.capitalize()}:")
    elif state == STATE_SECRET_KEY:
        save_secret_key(user_id, platform, text)
        if platform == 'kucoin':
            user_states[user_id] = STATE_PASSWORD
            await update.message.reply_text("الرجاء إدخال API Password (Passphrase) لمنصة KuCoin:")
        else:
            user_states[user_id] = STATE_NONE
            valid = await validate_api_keys(user_id)
            if valid:
                await update.message.reply_text(f"✅ تم التحقق من مفاتيح API لمنصة {platform.capitalize()} بنجاح!")
            else:
                await update.message.reply_text(
                    f"❌ خطأ في مفاتيح API لمنصة {platform.capitalize()}، الرجاء التأكد وإعادة المحاولة."
                )
    elif state == STATE_PASSWORD:
        save_password(user_id, platform, text)
        user_states[user_id] = STATE_NONE
        valid = await validate_api_keys(user_id)
        if valid:
            await update.message.reply_text(f"✅ تم التحقق من مفاتيح API لمنصة {platform.capitalize()} بنجاح!")
        else:
            await update.message.reply_text(
                f"❌ خطأ في مفاتيح API لمنصة {platform.capitalize()}، الرجاء التأكد وإعادة المحاولة."
            )
    elif state == STATE_INVEST_AMOUNT:
        if text.replace('.', '', 1).isdigit():
            amount = float(text)
            set_user_invest_amount(user_id, amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(f"تم تعيين المبلغ المستثمر: {amount} دولار")
        else:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
    else:
        await update.message.reply_text("يرجى استخدام القوائم للانتقال للخيارات.")

def get_user_active_platforms(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT active_platforms FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return []

def save_api_key(user_id, platform, api_key):
    create_new_user_if_not_exists(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    field = f"{platform}_api_key"
    cursor.execute(
        f"UPDATE users SET {field}=%s WHERE telegram_id=%s",
        (api_key, user_id)
    )
    # تحديث active_platforms إذا غير موجودة
    active_platforms = get_user_active_platforms(user_id)
    if platform not in active_platforms:
        active_platforms.append(platform)
        cursor.execute(
            "UPDATE users SET active_platforms=%s WHERE telegram_id=%s",
            (json.dumps(active_platforms), user_id)
        )
    conn.commit()
    cursor.close()
    conn.close()

def save_secret_key(user_id, platform, secret_key):
    create_new_user_if_not_exists(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    field = f"{platform}_secret_key"
    cursor.execute(
        f"UPDATE users SET {field}=%s WHERE telegram_id=%s",
        (secret_key, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def save_password(user_id, platform, password):
    if platform != 'kucoin':
        return
    create_new_user_if_not_exists(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET kucoin_password=%s WHERE telegram_id=%s",
        (password, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_invest_amount(user_id, amount):
    create_new_user_if_not_exists(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET invested_amount=%s WHERE telegram_id=%s",
        (amount, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

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
        if binance_api and binance_secret:
            binance = ccxt.binance(
                {
                    "apiKey": binance_api,
                    "secret": binance_secret,
                    "enableRateLimit": True,
                }
            )
            balance = await run_in_executor(binance.fetch_balance)
    except Exception as e:
        print(f"Binance API Error: {e}")
        return False

    try:
        if kucoin_api and kucoin_secret and kucoin_password:
            kucoin = ccxt.kucoin(
                {
                    "apiKey": kucoin_api,
                    "secret": kucoin_secret,
                    "password": kucoin_password,
                    "enableRateLimit": True,
                }
            )
            balance = await run_in_executor(kucoin.fetch_balance)
    except Exception as e:
        print(f"KuCoin API Error: {e}")
        return False

    return True

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