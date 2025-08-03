import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GPT_API_KEY = os.getenv("GPT_API_KEY")
ADMIN_WALLET = os.getenv("ADMIN_WALLET")  # محفظة العمولة

