import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import ccxt
from database import create_tables, get_user, save_user_data, get_settings, update_settings
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=5)

# States
STATE_NONE = 0
STATE_ENTER_BINANCE_API = 1
STATE_ENTER_BINANCE_SECRET = 2
STATE_ENTER_KUCOIN_API = 3
STATE_ENTER_KUCOIN_SECRET = 4
STATE_ENTER_KUCOIN_PASSWORD = 5
STATE_ENTER_WALLET = 6
STATE_ENTER_INVEST_AMOUNT = 7
STATE_OWNER_SET_PROFIT = 8

user_states = {}
temp_data = {}

async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))

# --- بوت الأوامر والقوائم ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)
    profit_percent = get_settings()['profit_percent']

    keyboard = [
        [InlineKeyboardButton("1️⃣ تسجيل أو تعديل بيانات التداول والمحفظة", callback_data='trade_data')],
        [InlineKeyboardButton("2️⃣ تعيين مبلغ الاستثمار", callback_data='set_amount')],
        [InlineKeyboardButton("3️⃣ بدء استثمار حقيقي", callback_data='start_invest')],
        [InlineKeyboardButton("4️⃣ بدء استثمار وهمي", callback_data='start_demo')],
        [InlineKeyboardButton("5️⃣ كشف حساب عن فترة", callback_data='account_statement')],
        [InlineKeyboardButton("6️⃣ حالة السوق", callback_data='market_status')],
        [InlineKeyboardButton("7️⃣ إيقاف الاستثمار", callback_data='stop_invest')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    wallet_msg = user['wallet_address'] if user and user.get('wallet_address') else "لم يتم تعيين محفظة"
    invest_amount = user['invested_amount'] if user else 0
    await update.message.reply_text(
        f"مرحبًا! نسبة ربح البوت الحالية: {profit_percent}%\n"
        f"محفظتك الحالية: {wallet_msg}\n"
        f"مبلغ الاستثمار الحالي: {invest_amount} دولار\n\n"
        "اختر من القائمة:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    data = query.data

    if data == 'trade_data':
        await show_trade_data_menu(update, user_id)
    elif data == 'set_amount':
        user_states[user_id] = STATE_ENTER_INVEST_AMOUNT
        await query.message.reply_text("الرجاء إدخال مبلغ الاستثمار (رقم فقط):")
    elif data == 'start_invest':
        await query.message.reply_text("بدء الاستثمار الحقيقي... (تحت التطوير)")
    elif data == 'start_demo':
        await query.message.reply_text("بدء استثمار وهمي... (تحت التطوير)")
    elif data == 'account_statement':
        await query.message.reply_text("أدخل تاريخ البداية (yyyy-mm-dd):")
        user_states[user_id] = STATE_NONE  # لتبسيط المثال
    elif data == 'market_status':
        await query.message.reply_text("تحليل السوق... (تحت التطوير)")
    elif data == 'stop_invest':
        # غيّر حالة الاستثمار للمستخدم
        save_user_data(user_id, is_active=False)
        await query.message.reply_text("تم إيقاف استثمارك.")
    elif data.startswith('edit_platform_'):
        platform = data.split('_')[-1]
        await edit_platform_keys(update, user_id, platform)
    elif data == 'set_wallet':
        user_states[user_id] = STATE_ENTER_WALLET
        await query.message.reply_text("الرجاء إدخال عنوان المحفظة الخاصة بك:")
    elif data == 'owner_settings':
        if user_id != OWNER_TELEGRAM_ID:
            await query.message.reply_text("غير مصرح لك بالوصول لهذه القائمة.")
            return
        await show_owner_settings(update)
    elif data == 'set_profit_percent':
        user_states[user_id] = STATE_OWNER_SET_PROFIT
        await query.message.reply_text("ادخل نسبة ربح البوت الجديدة (مثلا 5):")

async def show_trade_data_menu(update, user_id):
    user = get_user(user_id)
    active_platforms = []
    if user and user.get('active_platforms'):
        try:
            active_platforms = json.loads(user['active_platforms'])
        except:
            active_platforms = []

    buttons = []
    for platform in ['binance', 'kucoin']:
        status = '✅ مفعل' if platform in active_platforms else '❌ غير مفعل'
        buttons.append([InlineKeyboardButton(f"{platform.capitalize()} [{status}]", callback_data=f'edit_platform_{platform}')])

    buttons.append([InlineKeyboardButton("➕ إضافة منصة جديدة", callback_data='add_platform')])
    buttons.append([InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data='start')])

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.message.reply_text("منصات التداول الخاصة بك:", reply_markup=reply_markup)

async def edit_platform_keys(update, user_id, platform):
    user_states[user_id] = STATE_ENTER_BINANCE_API if platform == 'binance' else STATE_ENTER_KUCOIN_API
    temp_data[user_id] = {'platform': platform}
    await update.callback_query.message.reply_text(f"أدخل API Key لمنصة {platform.capitalize()}:")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id, STATE_NONE)
    temp = temp_data.get(user_id, {})

    if state == STATE_ENTER_INVEST_AMOUNT:
        if text.replace('.', '', 1).isdigit():
            amount = float(text)
            save_user_data(user_id, invested_amount=amount)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(f"تم تعيين مبلغ الاستثمار: {amount} دولار")
        else:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")

    elif state == STATE_ENTER_BINANCE_API:
        temp['api_key'] = text
        user_states[user_id] = STATE_ENTER_BINANCE_SECRET
        temp_data[user_id] = temp
        await update.message.reply_text("أدخل Binance Secret Key:")

    elif state == STATE_ENTER_BINANCE_SECRET:
        temp['secret_key'] = text
        # احفظ مفاتيح Binance
        user = get_user(user_id)
        active_platforms = []
        if user and user.get('active_platforms'):
            try:
                active_platforms = json.loads(user['active_platforms'])
            except:
                active_platforms = []

        if 'binance' not in active_platforms:
            active_platforms.append('binance')

        save_user_data(
            user_id,
            binance_api_key=temp['api_key'],
            binance_secret_key=temp['secret_key'],
            active_platforms=json.dumps(active_platforms)
        )
        user_states[user_id] = STATE_NONE
        temp_data.pop(user_id, None)
        await update.message.reply_text("تم حفظ مفاتيح Binance. جارٍ التحقق...")
        valid = await validate_binance_keys(temp['api_key'], temp['secret_key'])
        if valid:
            await update.message.reply_text("✅ مفاتيح Binance صالحة وتم التفعيل!")
        else:
            await update.message.reply_text("❌ مفاتيح Binance غير صالحة، يرجى إعادة المحاولة.")

    elif state == STATE_ENTER_KUCOIN_API:
        temp['api_key'] = text
        user_states[user_id] = STATE_ENTER_KUCOIN_SECRET
        temp_data[user_id] = temp
        await update.message.reply_text("أدخل KuCoin Secret Key:")

    elif state == STATE_ENTER_KUCOIN_SECRET:
        temp['secret_key'] = text
        user_states[user_id] = STATE_ENTER_KUCOIN_PASSWORD
        temp_data[user_id] = temp
        await update.message.reply_text("أدخل KuCoin API Password (Passphrase):")

    elif state == STATE_ENTER_KUCOIN_PASSWORD:
        temp['password'] = text
        # احفظ مفاتيح KuCoin
        user = get_user(user_id)
        active_platforms = []
        if user and user.get('active_platforms'):
            try:
                active_platforms = json.loads(user['active_platforms'])
            except:
                active_platforms = []

        if 'kucoin' not in active_platforms:
            active_platforms.append('kucoin')

        save_user_data(
            user_id,
            kucoin_api_key=temp['api_key'],
            kucoin_secret_key=temp['secret_key'],
            kucoin_password=temp['password'],
            active_platforms=json.dumps(active_platforms)
        )
        user_states[user_id] = STATE_NONE
        temp_data.pop(user_id, None)
        await update.message.reply_text("تم حفظ مفاتيح KuCoin. جارٍ التحقق...")
        valid = await validate_kucoin_keys(temp['api_key'], temp['secret_key'], temp['password'])
        if valid:
            await update.message.reply_text("✅ مفاتيح KuCoin صالحة وتم التفعيل!")
        else:
            await update.message.reply_text("❌ مفاتيح KuCoin غير صالحة، يرجى إعادة المحاولة.")

    elif state == STATE_ENTER_WALLET:
        # حفظ عنوان المحفظة
        save_user_data(user_id, wallet_address=text)
        user_states[user_id] = STATE_NONE
        await update.message.reply_text(f"تم حفظ محفظتك: {text}")

    elif state == STATE_OWNER_SET_PROFIT:
        if not update.message.from_user.id == OWNER_TELEGRAM_ID:
            await update.message.reply_text("غير مصرح لك.")
            user_states[user_id] = STATE_NONE
            return

        try:
            val = float(text)
            if val < 0 or val > 100:
                raise ValueError
            update_settings(profit_percent=val)
            user_states[user_id] = STATE_NONE
            await update.message.reply_text(f"تم تحديث نسبة ربح البوت إلى {val}%")
        except:
            await update.message.reply_text("الرجاء إدخال رقم صالح بين 0 و 100.")

    else:
        await update.message.reply_text("يرجى استخدام القوائم فقط. ارسل /start للعودة للقائمة الرئيسية.")

# --- تحقق المفاتيح ---
async def validate_binance_keys(api_key, secret_key):
    try:
        binance = ccxt.binance({
            "apiKey": api_key,
            "secret": secret_key,
            "enableRateLimit": True,
        })
        balance = await run_in_executor(binance.fetch_balance)
        return True
    except Exception as e:
        logger.error(f"Binance API validation failed: {e}")
        return False

async def validate_kucoin_keys(api_key, secret_key, password):
    try:
        kucoin = ccxt.kucoin({
            "apiKey": api_key,
            "secret": secret_key,
            "password": password,
            "enableRateLimit": True,
        })
        balance = await run_in_executor(kucoin.fetch_balance)
        return True
    except Exception as e:
        logger.error(f"KuCoin API validation failed: {e}")
        return False

# --- نقطة الدخول ---
def main():
    create_tables()
    global OWNER_TELEGRAM_ID
    OWNER_TELEGRAM_ID = int(os.getenv('OWNER_TELEGRAM_ID') or 123456789)  # عدل هنا برقمك

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()