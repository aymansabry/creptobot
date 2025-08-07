import smtplib
from email.message import EmailMessage
from core.config import config

class AlertSystem:
    @staticmethod
    def send_email_alert(subject: str, message: str):
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = subject
        msg['From'] = config.EMAIL_SENDER
        msg['To'] = config.EMAIL_RECEIVER
        
        with smtplib.SMTP(config.SMTP_SERVER) as server:
            server.send_message(msg)
