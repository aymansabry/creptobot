# notifications.py
import os
import smtplib
from email.message import EmailMessage
from telegram import Bot
from database import query, execute
import logging

BOT = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "")  # comma separated

def send_telegram(telegram_id, text):
    try:
        BOT.send_message(chat_id=telegram_id, text=text)
    except Exception as e:
        logging.error("Telegram send failed: %s", e)

def send_notification_to_user(user_id, text):
    t = query("SELECT telegram_id FROM users WHERE id=%s", (user_id,), fetchone=True)
    if t:
        try:
            send_telegram(t['telegram_id'], text)
            execute("INSERT INTO notifications (user_id, message) VALUES (%s,%s)", (user_id, text))
        except Exception as e:
            logging.error("Notify user error: %s", e)

def send_admin_alert(subject, message):
    # send via telegram to owners/admins + email
    admins = query("SELECT telegram_id FROM users WHERE role_id IN (1,2)")
    for a in admins:
        try:
            send_telegram(a['telegram_id'], f"⚠️ {subject}\n{message}")
        except:
            pass
    # email
    if ADMIN_EMAILS:
        try:
            smtp_host = os.getenv("SMTP_HOST")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER")
            smtp_pass = os.getenv("SMTP_PASS")
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = ADMIN_EMAILS.split(',')
            msg.set_content(message)
            s = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
            s.quit()
        except Exception as e:
            logging.error("Admin email failed: %s", e)
