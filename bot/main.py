from telegram.ext import Application
from config import TELEGRAM_TOKEN
from handlers import setup_handlers

app = Application.builder().token(TELEGRAM_TOKEN).build()
setup_handlers(app)
app.run_polling()
