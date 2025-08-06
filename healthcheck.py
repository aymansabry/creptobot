import requests
import os
from config import config

def check_bot_health():
    try:
        if config.is_production:
            response = requests.get(f"{config.WEBHOOK_URL}/health")
            return response.status_code == 200
        return True
    except:
        return False

if __name__ == "__main__":
    exit(0 if check_bot_health() else 1)
