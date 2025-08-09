import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from core.config import BOT_TOKEN
from handlers.user_handler import start_handler, handle_user_selection, text_handler
from handlers.admin_handler import admin_handler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start_handler))
app.add_handler(CallbackQueryHandler(handle_user_selection))
app.add_handler(CommandHandler("admin", admin_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

if __name__ == "__main__":
    app.run_polling()
