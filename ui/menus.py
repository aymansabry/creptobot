from telegram import ReplyKeyboardMarkup

def user_main_menu():
    return ReplyKeyboardMarkup([["📊 محفظتي", "💰 بدء التداول"]], resize_keyboard=True)

def admin_main_menu():
    return ReplyKeyboardMarkup([["👤 المستخدمون", "📈 الأرباح"]], resize_keyboard=True)
