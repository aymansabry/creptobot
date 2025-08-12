# main.py
import logging
import os
import datetime
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

# User input states
STATE_NONE = 0
STATE_BINANCE_API = 1
STATE_BINANCE_SECRET = 2
STATE_KUCOIN_API = 3
STATE_KUCOIN_SECRET = 4
STATE_KUCOIN_PASSWORD = 5
STATE_INVEST_AMOUNT = 6
STATE_WAITING_FOR_DATE = 30

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("١. تسجيل أو تعديل بيانات التداول", callback_data='trade_data')],
        [InlineKeyboardButton("٢. ابدأ استثمار", callback_data='start_invest')],
        [InlineKeyboardButton("٣. استثمار وهمي", callback_data='virtual_invest')],
        [InlineKeyboardButton("٤. كشف حساب عن فترة", callback_data='account_statement')],
        [InlineKeyboardButton("٥. حالة السوق", callback_data='market_status')],
        [InlineKeyboardButton("٦. إيقاف الاستثمار", callback_data='stop_invest')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحبًا بك! اختر من القائمة الرئيسية:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # القوائم والخيارات
    if query.data == 'trade_data':
        await send_trade_data_menu(query, user_id)
    elif query.data == 'edit_binance_api':
        user_states[user_id] = STATE_BINANCE_API
        await query.message.reply_text("الرجاء إدخال Binance API Key:")
    elif query.data == 'edit_binance_secret':
        user_states[user_id] = STATE_BINANCE_SECRET
        await query.message.reply_text("الرجاء إدخال Binance Secret Key:")
    elif query.data == 'edit_kucoin_api':
        user_states[user_id] = STATE_KUCOIN_API
        await query.message.reply_text(
            "الرجاء إدخال KuCoin API Key:\n"
            "لمعرفة كيفية الحصول عليه: https://docs.kucoin.com/\n"
            "تأكد من تفعيل صلاحيات التداول والقراءة."
        )
    elif query.data == 'edit_kucoin_secret':
        user_states[user_id] = STATE_KUCOIN_SECRET
        await query.message.reply_text("الرجاء إدخال KuCoin Secret Key:")
    elif query.data == 'edit_kucoin_password':
        user_states[user_id] = STATE_KUCOIN_PASSWORD
        await query.message.reply_text(
            "الرجاء إدخال KuCoin API Password (Passphrase):\n"
            "(هي كلمة السر التي اخترتها عند إنشاء API في KuCoin)"
        )
    elif query.data == 'edit_invest_amount':
        user_states[user_id] = STATE_INVEST_AMOUNT
        await query.message.reply_text("الرجاء إدخال المبلغ المستثمر (رقم فقط):")
    elif query.data == 'validate_apis':
        valid = await validate_api_keys(user_id)
        if valid:
            await query.message.reply_text("✅ تم التحقق من مفاتيح API بنجاح!")
        else:
            await query.message.reply_text(
                "❌ خطأ في مفاتيح API، الرجاء التأكد وإعادة المحاولة.\n"
                "تأكد من إدخال المفاتيح بشكل صحيح وتفعيل الصلاحيات."
            )
    elif query.data == 'start_invest':
        invest_amount = get_user_invest_amount(user_id)
        active = is_investment_active(user_id)
        if invest_amount <= 0:
            await query.message.reply_text("الرجاء تعيين مبلغ استثمار صالح أولًا من قائمة تسجيل أو تعديل بيانات التداول.")
            return
        if not active:
            await query.message.reply_text("الاستثمار موقوف حاليا، الرجاء تفعيله أولاً.")
            return
        await query.message.reply_text(f"بدء استثمار بمبلغ {invest_amount} دولار. جاري تنفيذ أوامر المراجحة...")
        # إضافة تنفيذ أوامر المراجحة لاحقًا
    elif query.data == 'virtual_invest':
        await query.message.reply_text("عرض استثمار وهمي (محاكاة بدون أموال حقيقية).")
    elif query.data == 'account_statement':
        await send_date_picker(query, user_id)
        user_states[user_id] = STATE_WAITING_FOR_DATE
    elif query.data.startswith('statement_'):
        date_str = query.data.split('_')[1]
        user_states[user_id] = STATE_NONE
        report = get_account_statement(user_id, date_str)
        await query.message.edit_text(report)
    elif query.data == 'market_status':
        report = get_market_analysis()
        await query.message.reply_text(report)
    elif query.data == 'stop_invest':
        set_user_investment_active(user_id, False)
        await query.message.reply_text("تم إيقاف الاستثمار حسب طلبك. لن يتم استخدام أموالك حتى تقوم بالتفعيل مجددًا.")
    elif query.data == 'main_menu':
        await query.message.edit_text("تم الرجوع إلى القائمة الرئيسية.")
        await start(update=query, context=context)
    else:
        await query.message.reply_text("اختيار غير معروف، الرجاء المحاولة مجددًا.")

async def send_trade_data_menu(query, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT binance_api_key, binance_secret_key, kucoin_api_key, kucoin_secret_key, kucoin_password, invested_amount FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    keyboard = []
    if row:
        b_api, b_sec, k_api, k_sec, k_pass, invest_amt = row
    else:
        b_api = b_sec = k_api = k_sec = k_pass = None
        invest_amt = 0

    keyboard.append([InlineKeyboardButton(f"Binance API Key {'✔️' if b_api else '❌'}", callback_data='edit_binance_api')])
    keyboard.append([InlineKeyboardButton(f"Binance Secret Key {'✔️' if b_sec else '❌'}", callback_data='edit_binance_secret')])
    keyboard.append([InlineKeyboardButton(f"KuCoin API Key {'✔️' if k_api else '❌'}", callback_data='edit_kucoin_api')])
    keyboard.append([InlineKeyboardButton(f"KuCoin Secret Key {'✔️' if k_sec else '❌'}", callback_data='edit_kucoin_secret')])
    keyboard.append([InlineKeyboardButton(f"KuCoin Password {'✔️' if k_pass else '❌'}", callback_data='edit_kucoin_password')])
    keyboard.append([InlineKeyboardButton(f"المبلغ المستثمر: {invest_amt} دولار", callback_data='edit_invest_amount')])
    keyboard.append([InlineKeyboardButton("تحقق من صحة مفاتيح API", callback_data='validate_apis')])
    keyboard.append([InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')])

    await query.message.edit_text("تعديل بيانات التداول الخاصة بك:", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_date_picker(query, user_id):
    keyboard = []
    today = datetime.date.today()
    for i in range(7):
        day = today - datetime.timedelta(days=i)
        keyboard.append([InlineKeyboardButton(day.strftime('%Y-%m-%d'), callback_data=f'statement_{day}')])
    keyboard.append([InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')])
    await query.message.edit_text("اختر بداية الفترة:", reply_markup=InlineKeyboardMarkup(keyboard))

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
                "❌ خطأ في مفاتيح API، الرجاء إعادة المحاولة.\n\n"
                "تأكد من:\n"
                "- إدخال API Key، Secret Key، وPassword بشكل صحيح.\n"
                "- تفعيل صلاحيات التداول والقراءة في حساب KuCoin API.\n"
                "- عدم وجود قيود أمان تمنع الوصول."
            )
    elif state == STATE_INVEST_AMOUNT:
        if text.replace('.', '', 1).isdigit():
            amount = float(text)
            set_user_invest_amount(user_id, amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(f"تم تعيين المبلغ المستثمر: {amount} دولار")
        else:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
    elif state == STATE_WAITING_FOR_DATE:
        await update.message.reply_text("يرجى اختيار التاريخ من الأزرار، وليس بكتابة النص.")
    else:
        await update.message.reply_text("يرجى استخدام القوائم للانتقال للخيارات.")

# دوال حفظ وتحديث بيانات المستخدم في DB

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
        "UPDATE users SET binance_secret_key=%s WHERE telegram_id=%s",
        (secret_key, user_id),
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_kucoin_api(user_id, api_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET kucoin_api_key=%s WHERE telegram_id=%s",
        (api_key, user_id),
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_kucoin_secret(user_id, secret_key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET kucoin_secret_key=%s WHERE telegram_id=%s",
        (secret_key, user_id),
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_kucoin_password(user_id, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET kucoin_password=%s WHERE telegram_id=%s",
        (password, user_id),
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_invest_amount(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET invested_amount=%s WHERE telegram_id=%s",
        (amount, user_id),
    )
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

def is_investment_active(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT investment_active FROM users WHERE telegram_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row and row[0] is not None:
        return bool(row[0])
    return True  # الافتراض مفعّل

def set_user_investment_active(user_id, active: bool):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET investment_active=%s WHERE telegram_id=%s",
        (active, user_id),
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_account_statement(user_id, start_date_str):
    # تقرير وهمي تجريبي
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    report = (
        f"كشف حساب المستخدم {user_id} من {start_date_str} حتى الآن:\n\n"
        f"- عدد الصفقات: 10\n"
        f"- الأرباح: 150 دولار\n"
        f"- الخسائر: 20 دولار\n\n"
        f"(هذا تقرير تجريبي)"
    )
    return report

def get_market_analysis():
    analysis = (
        "تحليل السوق الحالي:\n"
        "- سعر BTC: 28000 دولار\n"
        "- سعر ETH: 1800 دولار\n"
        "نصيحة: التنويع في العملات والاستثمار طويل الأجل أقل مخاطرة."
    )
    return analysis

async def validate_api_keys(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT binance_api_key, binance_secret_key, kucoin_api_key, kucoin_secret_key, kucoin_password "
        "FROM users WHERE telegram_id=%s",
        (user_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return False

    binance_api, binance_secret, kucoin_api, kucoin_secret, kucoin_password = row

    # تحقق Binance
    try:
        binance = ccxt.binance({
            "apiKey": binance_api,
            "secret": binance_secret,
            "enableRateLimit": True,
        })
        balance = await run_in_executor(binance.fetch_balance)
    except Exception as e:
        print(f"Binance API Error: {e}")
        return False

    # تحقق KuCoin
    try:
        kucoin = ccxt.kucoin({
            "apiKey": kucoin_api,
            "secret": kucoin_secret,
            "password": kucoin_password,
            "enableRateLimit": True,
        })
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