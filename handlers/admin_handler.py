from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.models import User
from db.session import get_session

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    session = get_session()
    user = session.query(User).filter_by(telegram_id=str(user_id)).first()

    if not user or not user.is_admin:
        await update.message.reply_text("عذراً، ليس لديك صلاحية الدخول كمدير.")
        session.close()
        return

    keyboard = [
        [InlineKeyboardButton("عرض المستخدمين", callback_data="admin_list_users")],
        [InlineKeyboardButton("تنشيط/تعطيل المستخدم", callback_data="admin_toggle_user")],
        [InlineKeyboardButton("التداول كالمستخدم", callback_data="admin_trade")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لوحة تحكم المدير:", reply_markup=reply_markup)
    session.close()
