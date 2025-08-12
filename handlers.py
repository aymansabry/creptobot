# handlers.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
import database
import utils

# --- قائمة المستخدم الرئيسية ---
def user_main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("1️⃣ تسجيل / تعديل بيانات التداول", callback_data="user_edit_data")],
        [InlineKeyboardButton("2️⃣ ابدأ استثمار", callback_data="user_start_invest")],
        [InlineKeyboardButton("3️⃣ استثمار وهمي", callback_data="user_start_virtual")],
        [InlineKeyboardButton("4️⃣ كشف حساب عن فترة", callback_data="user_statement")],
        [InlineKeyboardButton("5️⃣ حالة السوق", callback_data="user_market_status")],
        [InlineKeyboardButton("6️⃣ إيقاف الاستثمار", callback_data="user_stop_invest")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📋 اختر من القائمة:", reply_markup=reply_markup)

# --- قائمة المدير ---
def admin_main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("تعديل نسبة ربح البوت", callback_data="admin_edit_fee")],
        [InlineKeyboardButton("📊 عدد المستخدمين الإجمالي", callback_data="admin_total_users")],
        [InlineKeyboardButton("🟢 عدد المستخدمين أونلاين", callback_data="admin_online_users")],
        [InlineKeyboardButton("📈 تقارير الاستثمار", callback_data="admin_invest_reports")],
        [InlineKeyboardButton("⚙️ حالة البوت", callback_data="admin_bot_status")],
        [InlineKeyboardButton("💼 التداول كمستخدم", callback_data="admin_trade_as_user")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🛠 قائمة المدير:", reply_markup=reply_markup)

# --- التحقق من API Keys ---
def verify_api(update: Update, context: CallbackContext, exchange_name, api_key, api_secret, sandbox=False):
    try:
        client = utils.get_exchange_client(exchange_name, api_key, api_secret, sandbox)
        balance = client.fetch_balance()
        return True, balance
    except Exception as e:
        return False, str(e)

# --- إدخال بيانات المنصة ---
def user_edit_data(update: Update, context: CallbackContext):
    update.callback_query.edit_message_text("اختر المنصة التي تريد ربطها:")

# --- بدء استثمار حقيقي ---
def user_start_invest(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    # مثال لتنفيذ شراء حقيقي
    trades = utils.execute_trade(telegram_id, "BTC/USDT", 0.001, side="buy", test_only=False)
    update.callback_query.edit_message_text(f"✅ تم تنفيذ الصفقات: {trades}")

# --- بدء استثمار وهمي ---
def user_start_virtual(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    trades = utils.execute_trade(telegram_id, "BTC/USDT", 0.001, side="buy", test_only=True)
    update.callback_query.edit_message_text(f"🧪 محاكاة الصفقات: {trades}")

# --- كشف حساب ---
def user_statement(update: Update, context: CallbackContext):
    update.callback_query.edit_message_text("📅 أرسل لي بداية الفترة للاستعلام عن العمليات.")

# --- حالة السوق ---
def user_market_status(update: Update, context: CallbackContext):
    update.callback_query.edit_message_text("📊 تحليل السوق سيظهر هنا...")

# --- إيقاف الاستثمار ---
def user_stop_invest(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    database.stop_user_investment(telegram_id)
    update.callback_query.edit_message_text("⛔ تم إيقاف الاستثمار.")

