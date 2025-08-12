# handlers.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
import utils
import database

# ==============================
# قوائم المستخدم
# ==============================
def user_main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📋 تسجيل أو تعديل بيانات التداول", callback_data='register_data')],
        [InlineKeyboardButton("💰 مبلغ الاستثمار", callback_data='investment_amount')],
        [InlineKeyboardButton("🚀 ابدأ استثمار", callback_data='start_investment')],
        [InlineKeyboardButton("🎯 استثمار وهمي", callback_data='virtual_investment')],
        [InlineKeyboardButton("📑 كشف حساب عن فترة", callback_data='account_statement')],
        [InlineKeyboardButton("📊 حالة السوق", callback_data='market_status')],
        [InlineKeyboardButton("⛔ إيقاف الاستثمار", callback_data='stop_investment')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر من القائمة:", reply_markup=reply_markup)

# تسجيل أو تعديل بيانات التداول
def register_data(update: Update, context: CallbackContext):
    # هنا نعرض قائمة اختيار المنصة
    keyboard = [
        [InlineKeyboardButton("Binance", callback_data='platform_binance')],
        [InlineKeyboardButton("KuCoin", callback_data='platform_kucoin')],
        [InlineKeyboardButton("Bybit", callback_data='platform_bybit')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text("اختر المنصة:", reply_markup=reply_markup)

# تحقق API
def check_api(update: Update, context: CallbackContext, platform, api_key, api_secret):
    valid = utils.validate_api_keys(platform, api_key, api_secret)
    if valid:
        update.message.reply_text("✅ المفاتيح صحيحة وتم حفظها.")
        database.save_user_api(update.message.chat_id, platform, api_key, api_secret)
    else:
        update.message.reply_text("❌ المفاتيح غير صحيحة. أعد المحاولة.")

# مبلغ الاستثمار
def set_investment_amount(update: Update, context: CallbackContext):
    update.message.reply_text("💵 أدخل مبلغ الاستثمار المطلوب:")

# ابدأ استثمار
def start_investment(update: Update, context: CallbackContext):
    update.message.reply_text("🚀 جاري بدء الاستثمار بالمعلومات المسجلة...")

# استثمار وهمي
def virtual_investment(update: Update, context: CallbackContext):
    update.message.reply_text("📈 عرض نتائج الاستثمار الوهمي...")

# كشف حساب
def account_statement(update: Update, context: CallbackContext):
    update.message.reply_text("📅 أدخل تاريخ بداية الفترة:")

# حالة السوق
def market_status(update: Update, context: CallbackContext):
    update.message.reply_text("📊 تحليل السوق جاري...")

# إيقاف الاستثمار
def stop_investment(update: Update, context: CallbackContext):
    update.message.reply_text("⛔ تم إيقاف الاستثمار لهذا الحساب.")

# ==============================
# قوائم المدير
# ==============================
def admin_main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("✏️ تعديل نسبة ربح البوت", callback_data='edit_fee')],
        [InlineKeyboardButton("👥 عدد المستخدمين إجمالي", callback_data='total_users')],
        [InlineKeyboardButton("🟢 عدد المستخدمين أونلاين", callback_data='online_users')],
        [InlineKeyboardButton("📑 تقارير الاستثمار إجمالاً", callback_data='investment_reports')],
        [InlineKeyboardButton("🛠 حالة البوت برمجياً", callback_data='bot_status')],
        [InlineKeyboardButton("📋 التداول كمستخدم عادي", callback_data='user_mode')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("قائمة المدير:", reply_markup=reply_markup)
