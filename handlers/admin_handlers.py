from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in context.bot_data['admin_ids']:
        return await update.message.reply_text("❌ غير مصرح لك.")

    await update.message.reply_text("📊 النظام يعمل بنجاح. تحت السيطرة.")

def setup_admin_handlers(app: Application):
    app.add_handler(CommandHandler("admin", admin_stats))