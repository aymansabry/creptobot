from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 عرض الأسعار", callback_data='show_prices')],
        [InlineKeyboardButton("🔍 مراجحة الآن", callback_data='run_arbitrage')],
        [InlineKeyboardButton("🧪 تجربة تداول وهمي", callback_data='test_trade')],
        [InlineKeyboardButton("🚀 تنفيذ تداول فعلي", callback_data='real_trade')],
        [InlineKeyboardButton("⚙️ إعدادات الحساب", callback_data='settings')]
    ]
    return InlineKeyboardMarkup(keyboard)
