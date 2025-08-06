from telegram import ReplyKeyboardMarkup
from core.config import config

async def show_main_menu(update):
    menu_options = [
        ["💰 استثمار جديد", "📊 تحليل السوق"],
        ["💼 محفظتي", "📋 الصفقات النشطة"],
        ["⚙️ الإعدادات", "🆘 الدعم الفني"]
    ]
    
    await update.message.reply_text(
        f"مرحبًا! الحد الأدنى للاستثمار: {config.MIN_INVESTMENT} USDT\n"
        "اختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(menu_options, resize_keyboard=True)
    )
