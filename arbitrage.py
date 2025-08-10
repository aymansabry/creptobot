# utils.py
import os
import logging
from telegram import Bot
from database import query, execute, query_one
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

def _admin_telegram_ids():
    # OWNER_ID required, ADMINS_IDS optional (comma separated)
    ids = []
    owner = os.getenv("OWNER_ID")
    if owner:
        try:
            ids.append(int(owner))
        except:
            pass
    raw = os.getenv("ADMINS_IDS", "")
    for x in [s.strip() for s in raw.split(",") if s.strip()]:
        try:
            ids.append(int(x))
        except:
            pass
    return list(dict.fromkeys(ids))  # unique

def send_telegram(telegram_id, text):
    if not BOT:
        logger.error("Telegram bot token not configured.")
        return False
    try:
        BOT.send_message(chat_id=telegram_id, text=text)
        return True
    except Exception as e:
        logger.exception("Failed to send telegram message: %s", e)
        return False

def send_notification_to_user(user_id, text):
    row = query_one("SELECT telegram_id FROM users WHERE id=%s", (user_id,))
    if row:
        tg = row.get("telegram_id")
        if tg:
            ok = send_telegram(tg, text)
            try:
                execute("INSERT INTO notifications (user_id, message) VALUES (%s,%s)", (user_id, text))
            except Exception:
                logger.exception("Failed to log notification")
            return ok
    return False

def send_admin_alert(subject, message):
    text = f"⚠️ {subject}\n{message}"
    ids = _admin_telegram_ids()
    for i in ids:
        try:
            send_telegram(i, text)
        except:
            pass
    # also log to activity_logs
    try:
        execute("INSERT INTO activity_logs (user_id, action, details) VALUES (%s,%s,%s)",
                (None, subject, message))
    except Exception:
        logger.exception("Failed to write admin log")
