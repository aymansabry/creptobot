import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

class OperationMode(Enum):
    SIMULATION = "simulation"
    REAL = "real"

class SystemConfig:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",")]
    
    # إعدادات النظام
    CURRENT_MODE = OperationMode.REAL if os.getenv("REAL_TRADING", "false").lower() == "true" else OperationMode.SIMULATION
    ALLOW_SIMULATION = os.getenv("ALLOW_SIMULATION", "true").lower() == "true"
    
    # إعدادات المحفظة
    WALLET_TYPES = {
        "real": {
            "min_deposit": 10.0,
            "fee_percentage": 0.02
        },
        "simulation": {
            "min_deposit": 1.0,
            "fee_percentage": 0.0
        }
    }
