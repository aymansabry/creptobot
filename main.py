import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
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

# States
STATE_NONE = 0
STATE_ADD_PLATFORM_NAME = 1
STATE_ADD_PLATFORM_API = 2
STATE_ADD_PLATFORM_SECRET = 3
STATE_ADD_PLATFORM_PASSWORD = 4
STATE_SET_INVEST_AMOUNT = 5

user_states = {}
temp_platform_data = {}

executor = ThreadPoolExecutor(max_workers=5)

async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))

# DB functions

def ensure_user_exists(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users WHERE telegram_id=%s", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (telegram_id) VALUES (%s)", (user_id,))
        conn.commit()
    cursor.close()
    conn.close()

def get_user_platforms(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM platforms WHERE telegram_id=%s", (user_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result or []

def add_platform(user_id, platform_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO platforms (telegram_id, platform_name, active, valid) VALUES (%s, %s, 1, 0)",
        (user_id, platform_name)
    )
    conn.commit()
    cursor.close()
    conn.close()

def update_platform(platform_id, api_key=None, secret_key=None, password=None, active=None, valid=None):
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    if api_key is not None:
        updates.append("api_key=%s")
        params.append(api_key)
    if secret_key is not None:
        updates.append("secret_key=%s")
        params.append(secret_key)
    if password is not None:
        updates.append("password=%s")
        params.append(password)
    if active is not None:
        updates.append("active=%s")
        params.append(active)
    if valid is not None:
        updates.append("valid=%s")
        params.append(valid)
    if not updates:
        cursor.close()
        conn.close()
        return
    params.append(platform_id)
    sql = f"UPDATE platforms SET {', '.join(updates)} WHERE id=%s"
    cursor.execute(sql, params)
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

# API Validation

async def validate_platform_api(platform):
    try:
        name = platform['platform_name'].lower()
        if name == 'binance':
            exchange = ccxt.binance({
                "apiKey": platform['api_key'],
                "secret": platform['secret_key'],
                "enableRateLimit": True,
            })
        elif name == 'kucoin':
            exchange = ccxt.kucoin({
                "apiKey": platform['api_key'],
                "secret": platform['secret_key'],
                "password": platform['password'],
                "enableRateLimit": True,
            })
        else:
            return False

        balance = await run_in_executor(exchange.fetch_balance)
        return True
    except Exception as e:
        logger.error(f"{platform['platform_name']} API validation error: {e}")
        return False

async def check_and_update_platform(platform):
    is_valid = await validate_platform_api(platform)
    update_platform(platform['id'], valid=1 if is_valid else 0)
    return is_valid

# Bot Handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    ensure_user_exists(user_id)

    keyboard = [
        [InlineKeyboardButton("إدارة منصات التداول", callback_data='manage_platforms')],
        [InlineKeyboardButton("تعيين المبلغ المستثمر", callback_data='set_amount')],
        [InlineKeyboardButton("عرض الأرباح", callback_data='show_profit')],
        # أضف باقي الخيارات حسب الحاجة...
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحبًا بك! اختر من القائمة:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'manage_platforms':
        await show_platforms_menu(update, user_id)
    elif query.data == 'set_amount':
        user_states[user_id] = STATE_SET_INVEST_AMOUNT
        await query.message.reply_text("الرجاء إدخال المبلغ المستثمر (رقم فقط):")
    elif query.data == 'show_profit':
        profit = get_user_profit(user_id)
        await query.message.reply_text(f"الأرباح الحالية: {profit} دولار (تقريبي)")
    elif query.data.startswith('edit_platform_'):
        platform_id = int(query.data.split('_')[-1])
        await edit_platform_menu(update, user_id, platform_id)
    elif query.data == 'add_platform':
        user_states[user_id] = STATE_ADD_PLATFORM_NAME
        await query.message.reply_text("الرجاء إدخال اسم المنصة (مثلاً: Binance أو KuCoin):")

async def show_platforms_menu(update, user_id):
    platforms = get_user_platforms(user_id)
    buttons = []
    for p in platforms:
        status_emoji = "✅" if p['active'] and p['valid'] else "❌"
        buttons.append([InlineKeyboardButton(f"{status_emoji} {p['platform_name']} - تعديل", callback_data=f"edit_platform_{p['id']}")])
    buttons.append([InlineKeyboardButton("➕ إضافة منصة جديدة", callback_data="add_platform")])
    reply_markup = InlineKeyboardMarkup(buttons)
    if update.callback_query:
        await update.callback_query.message.edit_text("اختر منصة للتعديل أو إضافة منصة جديدة:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("اختر منصة للتعديل أو إضافة منصة جديدة:", reply_markup=reply_markup)

async def edit_platform_menu(update, user_id, platform_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM platforms WHERE id=%s AND telegram_id=%s", (platform_id, user_id))
    platform = cursor.fetchone()
    cursor.close()
    conn.close()

    if not platform:
        await update.callback_query.message.reply_text("المنصة غير موجودة.")
        return

    active_status = "✅ مفعل" if platform['active'] else "❌ معطل"
    valid_status = "✅ مفاتيح صالحة" if platform['valid'] else "❌ مفاتيح غير صالحة"
    text = (
        f"المنصة: {platform['platform_name']}\n"
        f"الحالة: {active_status}\n"
        f"صلاحية المفاتيح: {valid_status}\n"
        f"لديك المفاتيح:\n"
        f"API Key: {platform['api_key'] or 'غير معطى'}\n"
        f"Secret Key: {'معطى' if platform['secret_key'] else 'غير معطى'}\n"
        f"Password: {'معطى' if platform['password'] else 'غير معطى'}\n\n"
        "اختر الإجراء:"
    )
    keyboard = [
        [InlineKeyboardButton("تعديل API Key", callback_data=f"edit_api_{platform_id}")],
        [InlineKeyboardButton("تعديل Secret Key", callback_data=f"edit_secret_{platform_id}")],
        [InlineKeyboardButton("تعديل Password", callback_data=f"edit_password_{platform_id}")],
        [InlineKeyboardButton("تفعيل/تعطيل", callback_data=f"toggle_active_{platform_id}")],
        [InlineKeyboardButton("التحقق من المفاتيح", callback_data=f"validate_platform_{platform_id}")],
        [InlineKeyboardButton("العودة للقائمة الرئيسية", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(text, reply_markup=reply_markup)

async def handle_edit_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "main_menu":
        await start(update, context)
        return

    if data.startswith("toggle_active_"):
        platform_id = int(data.split('_')[-1])
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT active FROM platforms WHERE id=%s AND telegram_id=%s", (platform_id, user_id))
        row = cursor.fetchone()
        if not row:
            await query.message.reply_text("المنصة غير موجودة.")
            return
        current_active = row[0]
        new_active = 0 if current_active else 1
        update_platform(platform_id, active=new_active)
        status_text = "مفعلة" if new_active else "معطلة"
        await query.message.reply_text(f"تم {status_text} المنصة.")
        await show_platforms_menu(update, user_id)
        return

    if data.startswith("validate_platform_"):
        platform_id = int(data.split('_')[-1])
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM platforms WHERE id=%s AND telegram_id=%s", (platform_id, user_id))
        platform = cursor.fetchone()
        cursor.close()
        conn.close()
        if not platform:
            await query.message.reply_text("المنصة غير موجودة.")
            return
        await query.message.reply_text("جارٍ التحقق من المفاتيح...")
        is_valid = await check_and_update_platform(platform)
        emoji = "✅" if is_valid else "❌"
        await query.message.reply_text(f"التحقق من مفاتيح منصة {platform['platform_name']}: {emoji}")
        await show_platforms_menu(update, user_id)
        return

    # التعامل مع تعديل المفاتيح
    if data.startswith("edit_api_"):
        platform_id = int(data.split('_')[-1])
        user_states[user_id] = ('edit_api', platform_id)
        await query.message.reply_text("الرجاء إدخال API Key الجديد:")
        return

    if data.startswith("edit_secret_"):
        platform_id = int(data.split('_')[-1])
        user_states[user_id] = ('edit_secret', platform_id)
        await query.message.reply_text("الرجاء إدخال Secret Key الجديد:")
        return

    if data.startswith("edit_password_"):
        platform_id = int(data.split('_')[-1])
        user_states[user_id] = ('edit_password', platform_id)
        await query.message.reply_text("الرجاء إدخال Password الجديد:")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # حالة المستخدم الحالية
    state = user_states.get(user_id, STATE_NONE)

    # حالات التعديل
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
            # حفظ البيانات
            platform_name = temp_platform_data[user_id]['platform_name']
            api_key = temp_platform_data[user_id]['api_key']
            secret_key = temp_platform_data[user_id]['secret_key']
            # استعلام المنصة المضافة حديثًا
            platforms = get_user_platforms(user_id)
            platform_id = None
            for p in platforms:
                if p['platform_name'] == platform_name and (p['api_key'] == "" or p['api_key'] is None):
                    platform_id = p['id']
                    break
            if platform_id:
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
        platforms = get_user_platforms(user_id)
        platform_id = None
        for p in platforms:
            if p['platform_name'] == platform_name and (p['api_key'] == "" or p['api_key'] is None):
                platform_id = p['id']
                break
        if platform_id:
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

    # افتراضي: لا حالة
    await update.message.reply_text("اختر من القوائم أو أرسل /start للبدء.")

def