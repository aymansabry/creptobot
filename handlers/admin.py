from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

ADMIN_IDS = [123456789]  # ضع معرفك هنا

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        await update.message.reply_text("🔒 مرحباً أيها المدير.")
    else:
        await update.message.reply_text("🚫 ليس لديك صلاحية.")

admin_handler = CommandHandler("admin", admin)