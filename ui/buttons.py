# project_root/ui/buttons.py

from telegram import KeyboardButton, InlineKeyboardButton

START_TRADING = "🚀 بدء التداول"
VIEW_BALANCE = "💰 عرض الرصيد"
VIEW_PORTFOLIO = "📊 عرض المحفظة"
VIEW_HISTORY = "📜 سجل الصفقات"
HELP = "❓ مساعدة"
STOP_TRADING = "🛑 إيقاف التداول"
AUTO_TRADE = "🔁 تفعيل التداول المستمر"
MANUAL_TRADE = "📝 صفقة واحدة"
BACK_TO_MAIN = "🏠 العودة للقائمة الرئيسية"

VIEW_USERS = "👥 عرض المستخدمين"
VIEW_PROFITS = "📈 عرض الأرباح"
SET_FEES = "⚙️ تعديل نسبة البوت"
TOGGLE_USER_TRADING = "🔄 إيقاف/تشغيل التداول"
VIEW_ALL_TRADES = "🌐 عرض كل الصفقات"

CONFIRM_YES = InlineKeyboardButton("✅ تأكيد", callback_data="confirm_yes")
CONFIRM_NO = InlineKeyboardButton("❌ إلغاء", callback_data="confirm_no")
