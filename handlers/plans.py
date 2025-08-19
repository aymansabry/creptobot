# handlers/plans.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from database.connection import get_connection
from database.models import get_user_by_telegram_id
from utils.logger import log_action

async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("آمنة 🛡️", callback_data="safe")],
        [InlineKeyboardButton("متوازنة ⚖️", callback_data="balanced")],
        [InlineKeyboardButton("مغامرة 🚀", callback_data="aggressive")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر خطة الاستثمار:", reply_markup=reply_markup)

async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data
    user = query.from_user
    user_data = get_user_by_telegram_id(user.id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET plan = ? WHERE id = ?", (plan, user_data[0]))
    conn.commit()
    conn.close()

    log_action(user_data[0], "plan_change", f"Changed to {plan}")
    await query.edit_message_text(f"تم اختيار خطة: {plan} ✅")