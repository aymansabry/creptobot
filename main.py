# main.py
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
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
STATE_ADD_PLATFORM_NAME = 10
STATE_ADD_PLATFORM_API = 11
STATE_ADD_PLATFORM_SECRET = 12
STATE_ADD_PLATFORM_PASSWORD = 13
STATE_SET_INVEST_AMOUNT = 20

user_states = {}
temp_platform_data = {}

executor = ThreadPoolExecutor(max_workers=5)

async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await show_main_menu(update, user_id)


async def show_main_menu(update, user_id):
    keyboard = [
        [InlineKeyboardButton("إدارة منصات التداول", callback_data='manage_platforms')],
        [InlineKeyboardButton("تعيين مبلغ الاستثمار", callback_data='set_amount')],
        [InlineKeyboardButton("عرض الأرباح", callback_data='show_profit')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    if data == 'manage_platforms':
        await show_platforms_menu(update, user_id)
    elif data == 'set_amount':
        user_states[user_id] = STATE_SET_INVEST_AMOUNT
        await query.message.reply_text("الرجاء إدخال المبلغ المستثمر (رقم فقط):")
    elif data == 'show_profit':
        profit = get_user_profit(user_id)
        await query.message.reply_text(f"الأرباح الحالية: {profit} دولار (تقريبي)")
    elif data == 'add_platform':
        user_states[user_id] = STATE_ADD_PLATFORM_NAME
        await query.message.reply_text("الرجاء إدخال اسم المنصة (Binance أو KuCoin):")
    elif data.startswith('edit_platform_'):
        # مثال: edit_platform_3
        platform_id = int(data.split('_')[-1])
        await show_platform_edit_menu(update, platform_id)
    elif data.startswith('edit_api_'):
        platform_id = int(data.split('_')[-1])
        user_states[user_id] = ('edit_api', platform_id)
        await query.message.reply_text("الرجاء إدخال API Key الجديد:")
    elif data.startswith('edit_secret_'):
        platform_id = int(data.split('_')[-1])
        user_states[user_id] = ('edit_secret', platform_id)
        await query.message.reply_text("الرجاء إدخال Secret Key الجديد:")
    elif data.startswith('edit_password_'):
        platform_id = int(data.split('_')[-1])
        user_states[user_id] = ('edit_password', platform_id)
        await query.message.reply_text("الرجاء إدخال Password الجديد:")
    elif data.startswith('toggle_active_'):
        platform_id = int(data.split('_')[-1])
        toggle_platform_active(platform_id)
        await show_platforms_menu(update, user_id)
    elif data.startswith('validate_platform_'):
        platform_id = int(data.split('_')[-1])
        valid = await validate_platform(platform_id)
        if valid:
            await query.message.reply_text("✅ تم التحقق من مفاتيح API بنجاح!")
        else:
            await query.message.reply_text("❌ فشل التحقق من مفاتيح API. يرجى مراجعتها.")
        await show_platforms_menu(update, user_id)
    elif data == 'main_menu':
        await show_main_menu(update, user_id)


async def show_platforms_menu(update, user_id):
    platforms = get_user_platforms(user_id)
    keyboard = []
    for p in platforms:
        status = "✅" if p['active'] else "❌"
        line = f"{status} {p['platform_name']} (ID: {p['id']})"
        buttons = [
            InlineKeyboardButton("تعديل", callback_data=f"edit_platform_{p['id']}"),
            InlineKeyboardButton("تفعيل/إيقاف", callback_data=f"toggle_active_{p['id']}"),
            InlineKeyboardButton("تحقق", callback_data=f"validate_platform_{p['id']}"),
        ]
        keyboard.append(buttons)

    keyboard.append([InlineKeyboardButton("➕ إضافة منصة جديدة", callback_data='add_platform')])
    keyboard.append([InlineKeyboardButton("⬅ القائمة الرئيسية", callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.edit_text("قائمة منصاتك:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("قائمة منصاتك:", reply_markup=reply_markup)


async def show_platform_edit_menu(update, platform_id):
    platform = get_platform_by_id(platform_id)
    if not platform:
        await update.callback_query.message.reply_text("المنصة غير موجودة.")
        return

    keyboard = [
        InlineKeyboardButton("تعديل API Key", callback_data=f"edit_api_{platform_id}"),
        InlineKeyboardButton("تعديل Secret Key", callback_data=f"edit_secret_{platform_id}"),
    ]
    if platform['platform_name'].lower() == 'kucoin':
        keyboard.append(InlineKeyboardButton("تعديل Password", callback_data=f"edit_password_{platform_id}"))

    keyboard.append(InlineKeyboardButton("⬅ رجوع", callback_data='manage_platforms'))
    reply_markup = InlineKeyboardMarkup([[btn] for btn in keyboard])

    await update.callback_query.message.edit_text(f"تحرير منصة {platform['platform_name']}:", reply_markup=reply_markup)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id, STATE_NONE)

    # حالات التعديل المفتاحية
    if isinstance(state, tuple):
        action, platform_id = state
        if action == 'edit_api':
            update_platform(platform_id, api_key=text)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text("تم تحديث API Key.")
            await show_platforms_menu(update, user_id)
            return
        elif action == 'edit_secret':
            update_platform(platform_id, secret_key=text)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text("تم تحديث Secret Key.")
            await show_platforms_menu(update, user_id)
            return
        elif action == 'edit_password':
            update_platform(platform_id, password=text)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text("تم تحديث Password.")
            await show_platforms_menu(update, user_id)
            return

    if state == STATE_ADD_PLATFORM_NAME:
        platform_name = text.strip()
        if platform_name.lower() not in ['binance', 'kucoin']:
            await update.message.reply_text("الرجاء إدخال اسم منصة مدعومة (Binance أو KuCoin).")
            return
        add_platform(user_id, platform_name)
        user_states[user_id] = STATE_ADD_PLATFORM_API
        temp_platform_data[user_id] = {'platform_name': platform_name}
        await update.message.reply_text(f"تم إضافة منصة {platform_name}.\nالرجاء إدخال API Key:")
        return

    if state == STATE_ADD_PLATFORM_API:
        temp_platform_data[user_id]['api_key'] = text
        user_states[user_id] = STATE_ADD_PLATFORM_SECRET
        await update.message.reply_text("الرجاء إدخال Secret Key:")
        return

    if state == STATE_ADD_PLATFORM_SECRET:
        temp_platform_data[user_id]['secret_key'] = text
        if temp_platform_data[user_id]['platform_name'].lower() == 'kucoin':
            user_states[user_id] = STATE_ADD_PLATFORM_PASSWORD
            await update.message.reply_text("الرجاء إدخال Password (Passphrase) الخاص بـ KuCoin:")
        else:
            platform_name = temp_platform_data[user_id]['platform_name']
            api_key = temp_platform_data[user_id]['api_key']
            secret_key = temp_platform_data[user_id]['secret_key']
            platform_id = get_last_platform_id_for_user(user_id)
            update_platform(platform_id, api_key=api_key, secret_key=secret_key)
            user_states[user_id] = STATE_NONE
            temp_platform_data.pop(user_id, None)
            await update.message.reply_text("تم حفظ بيانات المنصة.")
        return

    if state == STATE_ADD_PLATFORM_PASSWORD:
        password = text
        platform_name = temp_platform_data[user_id]['platform_name']
        api_key = temp_platform_data[user_id]['api_key']
        secret_key = temp_platform_data[user_id]['secret_key']
        platform_id = get_last_platform_id_for_user(user_id)
        update_platform(platform_id, api_key=api_key, secret_key=secret_key, password=password)
        user_states[user_id] = STATE_NONE
        temp_platform_data.pop(user_id, None)
        await update.message.reply_text("تم حفظ بيانات منصة KuCoin بالكامل.")
        return

    if state == STATE_SET_INVEST_AMOUNT:
        if text.replace('.', '', 1).isdigit():
            amount = float(text)
            set_user_invest_amount(user_id, amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(f"تم تعيين المبلغ المستثمر: {amount} دولار")
        else:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return

    # افتراضي
    await update.message.reply_text("يرجى استخدام القوائم للبدء. أرسل /start للعودة إلى القائمة الرئيسية.")


# DB Functions

def create_tables_full():
    create_tables()
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS platforms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                telegram_id BIGINT,
                platform_name VARCHAR(50),
                api_key VARCHAR(255),
                secret_key VARCHAR(255),
                password VARCHAR(255),
                active BOOLEAN DEFAULT TRUE,
                UNIQUE(telegram_id, platform_name)
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()


def get_user_platforms(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM platforms WHERE telegram_id=%s", (user_id,))
    platforms = cursor.fetchall()
    cursor.close()
    conn.close()
    return platforms


def get_platform_by_id(platform_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM platforms WHERE id=%s", (platform_id,))
    platform = cursor.fetchone()
    cursor.close()
    conn.close()
    return platform


def add_platform(user_id, platform_name):
    conn = get_connection()
    cursor = conn.cursor()
    # أدخل السجل فقط مع telegram_id و platform_name
    try:
        cursor.execute(
            "INSERT INTO platforms (telegram_id, platform_name) VALUES (%s, %s)",
            (user_id, platform_name)
        )
        conn.commit()
    except Exception as e:
        print(f"Error adding platform: {e}")
    finally:
        cursor.close()
        conn.close()


def get_last_platform_id_for_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM platforms WHERE telegram_id=%s ORDER BY id DESC LIMIT 1", (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None


def update_platform(platform_id, api_key=None, secret_key=None, password=None, active=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "UPDATE platforms SET "
    params = []
    sets = []
    if api_key is not None:
        sets.append("api_key=%s")
        params.append(api_key)
    if secret_key is not None:
        sets.append("secret_key=%s")
        params.append(secret_key)
    if password is not None:
        sets.append("password=%s")
        params.append(password)
    if active is not None:
        sets.append("active=%s")
        params.append(active)
    query += ", ".join(sets)
    query += " WHERE id=%s"
    params.append(platform_id)
    cursor.execute(query, tuple(params))
    conn.commit()
    cursor.close()
    conn.close()


def toggle_platform_active(platform_id):
    platform = get_platform_by_id(platform_id)
    if platform:
        new_status = not platform['active']
        update_platform(platform_id, active=new_status)


def set_user_invest_amount(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET invested_amount=%s WHERE telegram_id=%s",
        (amount, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_user_profit(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT profit FROM users WHERE telegram_id=%s",
        (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else 0


async def validate_platform(platform_id):
    platform = get_platform_by_id(platform_id)
    if not platform:
        return False
    platform_name = platform['platform_name'].lower()
    api_key = platform['api_key']
    secret_key = platform['secret_key']
    password = platform['password']

    try:
        if platform_name == 'binance':
            exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
            })
        elif platform_name == 'kucoin':
            exchange = ccxt.kucoin({
                'apiKey': api_key,
                'secret': secret_key,
                'password': password,
                'enableRateLimit': True,
            })
        else:
            return False

        balance = await run_in_executor(exchange.fetch_balance)
        return True
    except Exception as e:
        print(f"Error validating {platform_name} keys: {e}")
        return False


def main():
    create_tables_full()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()