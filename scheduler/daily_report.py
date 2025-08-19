from telegram import Bot
from config import BOT_TOKEN
from services.report import generate_daily_report
from database.init_db import SessionLocal
from database.models import User

bot = Bot(token=BOT_TOKEN)
session = SessionLocal()

def send_reports():
    users = session.query(User).all()
    for user in users:
        report = generate_daily_report(user.id)
        try:
            bot.send_message(chat_id=int(user.telegram_id), text=report)
        except Exception as e:
            print(f"❌ فشل إرسال التقرير لـ {user.telegram_id}: {e}")
