from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
import os
from handlers import start_handler, review_handler
from buttons import button_handler

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start_handler))
app.add_handler(CommandHandler("review", review_handler))
app.add_handler(CallbackQueryHandler(button_handler))

if __name__ == "__main__":
    print("✅ Bot is running...")
    app.run_polling()