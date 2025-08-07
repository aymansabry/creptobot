import uuid
from typing import Dict, Any
from datetime import datetime

def generate_unique_id() -> str:
    return str(uuid.uuid4())

def format_timestamp(timestamp: datetime) -> str:
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def calculate_profit(buy_price: float, sell_price: float, amount: float) -> float:
    return (sell_price - buy_price) * amount

def validate_wallet_address(address: str) -> bool:
    # تنفيذ بسيط للتحقق من عنوان المحفظة
    return len(address) >= 25 and len(address) <= 64

def prepare_trade_data(user_id: int, symbol: str, buy_exchange: str, sell_exchange: str,
                     amount: float, buy_price: float, sell_price: float) -> Dict[str, Any]:
    profit = calculate_profit(buy_price, sell_price, amount)
    commission = profit * 0.1  # عمولة 10%
    net_profit = profit - commission
    
    return {
        'user_id': user_id,
        'symbol': symbol,
        'buy_exchange': buy_exchange,
        'sell_exchange': sell_exchange,
        'amount': amount,
        'buy_price': buy_price,
        'sell_price': sell_price,
        'profit': net_profit,
        'commission': commission,
        'status': 'pending'
    }

def format_currency(value: float, currency: str = 'USDT') -> str:
    return f"{value:.2f} {currency}"

def seconds_to_hms(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}h {minutes}m {seconds}s"
