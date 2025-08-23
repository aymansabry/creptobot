# db.py
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Dummy database to simulate a database.
# In a real-world scenario, you would use a proper database like PostgreSQL, MongoDB, or Redis.
user_database = {}

def create_user(user_id):
    """Initializes user data if it doesn't exist."""
    if user_id not in user_database:
        user_database[user_id] = {
            "api_keys": {},
            "amount": 0.0,
            "last_trades": [],
        }
        logger.info(f"User {user_id} created in the database.")

def save_api_keys(user_id, api_key, api_secret):
    """Saves API keys for a user."""
    create_user(user_id)
    user_database[user_id]["api_keys"] = {
        "api_key": api_key,
        "api_secret": api_secret,
    }
    logger.info(f"API keys saved for user {user_id}.")

def get_user_api_keys(user_id):
    """Retrieves API keys for a user."""
    return user_database.get(user_id, {}).get("api_keys", {})

def save_amount(user_id, amount):
    """Saves the trading amount for a user."""
    create_user(user_id)
    user_database[user_id]["amount"] = amount
    logger.info(f"Amount {amount} saved for user {user_id}.")

def get_amount(user_id):
    """Retrieves the trading amount for a user."""
    return user_database.get(user_id, {}).get("amount", 0.0)

def save_last_trades(user_id, pair, profit, timestamp):
    """
    Saves the last trade details for a user.
    This function was the missing piece causing the ImportError.
    """
    create_user(user_id)
    if "last_trades" not in user_database[user_id]:
        user_database[user_id]["last_trades"] = []
    
    trade_info = {
        "pair": pair,
        "profit": float(profit), # Convert Decimal to float for JSON compatibility
        "timestamp": timestamp.isoformat()
    }
    
    # Keep only the last 10 trades
    user_database[user_id]["last_trades"].insert(0, trade_info)
    user_database[user_id]["last_trades"] = user_database[user_id]["last_trades"][:10]
    
    logger.info(f"Trade for user {user_id} saved: {trade_info}")

def get_last_trades(user_id):
    """Retrieves the last recorded trades for a user."""
    trades = user_database.get(user_id, {}).get("last_trades", [])
    # Convert timestamp back to datetime object if needed, but for display string is fine
    return trades