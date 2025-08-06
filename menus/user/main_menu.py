from telegram import ReplyKeyboardMarkup
from core.config import Config

def show_main_menu(update):
    menu_options = [
        ["💰 استثمار جديد", "📊 تحليل السوق"],
        ["💼 محفظتي", "📋 الصفقات النشطة"],
        ["⚙️ الإعدادات", "🆘 الدعم الفني"]
    ]
    
    update.message.reply_text(
        f"مرحبًا! الحد الأدنى للاستثمار: {Config.MIN_INVESTMENT} USDT\n"
        "اختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(menu_options, resize_keyboard=True)
    )
