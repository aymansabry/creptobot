import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
TRON_GRID_API_KEY = os.getenv("TRON_GRID_API_KEY")
CENTRAL_WALLET_ADDRESS = os.getenv("CENTRAL_WALLET_ADDRESS")
OWNER_WALLET_ADDRESS = os.getenv("OWNER_WALLET_ADDRESS")
