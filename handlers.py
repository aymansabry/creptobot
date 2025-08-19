from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db import get_db

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
        db.commit()

    keyboard = [
        [InlineKeyboardButton("🔑 ربط مفاتيح Binance", callback_data='link_keys')],
        [InlineKeyboardButton("💰 تحديد مبلغ الاستثمار", callback_data='set_investment')],
        [InlineKeyboardButton("🚀 تفعيل التداول الحقيقي", callback_data='toggle_live')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("أهلاً بك في بوت التداول الثلاثي 👋\nاختر من القائمة:", reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'link_keys':
        query.edit_message_text("أرسل مفتاح Binance بهذا الشكل:\n`API_KEY|API_SECRET`")
    elif query.data == 'set_investment':
        query.edit_message_text("أرسل مبلغ الاستثمار بالدولار 💵")
    elif query.data == 'toggle_live':
        query.edit_message_text("تم تفعيل التداول الحقيقي ✅")