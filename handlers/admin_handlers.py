from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

def setup_admin_handlers(application):
    application.add_handler(CommandHandler("admin", admin_command))

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = context.bot_data.get("admin_ids", [])
    user_id = update.effective_user.id

    if user_id not in admin_ids:
        await update.message.reply_text("❌ ليس لديك صلاحية الوصول إلى لوحة الإدارة.")
        return

    await update.message.reply_text("✅ مرحبًا بك في لوحة التحكم الإدارية.\n(قريبًا سيتم تفعيل المزيد من الأوامر للمشرفين)")