# handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import database
import utils

# --- القوائم الرئيسية ---
def main_menu(user_role):
    if user_role == "admin":
        buttons = [
            [InlineKeyboardButton("📊 تعديل نسبة الربح", callback_data="edit_fee")],
            [InlineKeyboardButton("👥 عدد المستخدمين", callback_data="users_count")],
            [InlineKeyboardButton("📈 تقارير الاستثمار", callback_data="investment_report")],
            [InlineKeyboardButton("⚙️ حالة البوت", callback_data="bot_status")],
            [InlineKeyboardButton("🛒 التداول كمستخدم", callback_data="trade_as_user")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton("📋 تسجيل/تعديل بيانات التداول", callback_data="register_trade_data")],
            [InlineKeyboardButton("🚀 ابدأ استثمار", callback_data="start_real_investment")],
            [InlineKeyboardButton("🧪 استثمار وهمي", callback_data="start_virtual_investment")],
            [InlineKeyboardButton("📜 كشف حساب", callback_data="account_statement")],
            [InlineKeyboardButton("📊 حالة السوق", callback_data="market_status")],
            [InlineKeyboardButton("⛔ إيقاف الاستثمار", callback_data="stop_investment")]
        ]
    return InlineKeyboardMarkup(buttons)

# --- معالجة القائمة الرئيسية ---
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    role = database.get_user_role(user_id)
    update.message.reply_text(
        "اختر من القائمة:",
        reply_markup=main_menu(role)
    )

# --- تسجيل بيانات التداول ---
def register_trade_data(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text("🔑 اختر المنصة لإدخال API Key وSecret...")

# --- بدء الاستثمار الفعلي ---
def start_real_investment(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    exchanges = database.get_user_exchanges(user_id)
    if not exchanges:
        update.callback_query.message.reply_text("⚠️ لم تسجل بيانات التداول بعد.")
        return
    
    # التحقق من الرصيد
    for ex in exchanges:
        exchange = utils.get_exchange(ex['name'], ex['api_key'], ex['api_secret'])
        balance = exchange.fetch_balance()
        if balance['total']['USDT'] < 10:
            update.callback_query.message.reply_text(f"❌ رصيدك في {ex['name']} لا يكفي.")
            return
    
    update.callback_query.message.reply_text("✅ بدأ الاستثمار الفعلي...")

# --- بدء الاستثمار الوهمي ---
def start_virtual_investment(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text("🧪 بدأ الاستثمار الوهمي (محاكاة)...")

# --- كشف حساب ---
def account_statement(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text("📜 أدخل تاريخ البداية والنهاية لعرض كشف الحساب.")

# --- حالة السوق ---
def market_status(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text("📊 جاري تحليل السوق...")

# --- إيقاف الاستثمار ---
def stop_investment(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text("⛔ تم إيقاف الاستثمار.")

