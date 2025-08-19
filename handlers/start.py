# handlers/start.py
from telegram import Update
from telegram.ext import ContextTypes
from database.models import create_user, get_user_by_telegram_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_user(user.id, user.username)
    await update.message.reply_text(
        f"أهلاً {user.first_name} 👋\nاستثمارك يبدأ من هنا.\nاستخدم /plans لاختيار خطة، أو /invest لبدء الاستثمار."
    )