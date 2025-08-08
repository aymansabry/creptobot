import os
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ ليس لديك صلاحيات الوصول إلى لوحة التحكم.")
        return

    await update.message.reply_text("✅ مرحبًا بك في لوحة تحكم الأدمن.\n- تحت التطوير")

admin_handler = CommandHandler("admin", admin)
