import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_WALLET = os.getenv("OWNER_WALLET")  # محفظة مالك البوت
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ETH_NODE = os.getenv("ETH_NODE")  # عنوان العقدة الخاصة بـ Web3
