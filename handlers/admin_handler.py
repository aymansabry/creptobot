from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = context.bot_data.get(f"user_{user_id}")
    if not user or not user.is_admin:
        await update.message.reply_text("عذراً، ليس لديك صلاحية الدخول كمدير.")
        return

    keyboard = [
        [InlineKeyboardButton("عرض المستخدمين", callback_data="admin_list_users")],
        [InlineKeyboardButton("تنشيط/تعطيل المستخدم", callback_data="admin_toggle_user")],
        [InlineKeyboardButton("التداول كالمستخدم", callback_data="admin_trade")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لوحة تحكم المدير:", reply_markup=reply_markup)
