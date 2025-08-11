import ccxt
import json
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from models import User
import os

# مفتاح التشفير
SECRET_KEY = os.getenv("ENCRYPTION_KEY").encode()
fernet = Fernet(SECRET_KEY)

# 🔐 تشفير وفك تشفير
def encrypt_data(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()

# ⛓️‍♂️ ربط منصات المستخدم
def save_user_api_keys(db: Session, user_id: int, platform: str, api_key: str, api_secret: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    if platform.lower() == "binance":
        user.binance_api_key = encrypt_data(api_key)
        user.binance_api_secret = encrypt_data(api_secret)
    elif platform.lower() == "kucoin":
        user.kucoin_api_key = encrypt_data(api_key)
        user.kucoin_api_secret = encrypt_data(api_secret)

    db.commit()
    return True

# ⚡ تنفيذ عملية تداول بسيطة (مثال)
def execute_trade_binance(user: User, symbol: str, amount: float, side: str):
    try:
        api_key = decrypt_data(user.binance_api_key)
        api_secret = decrypt_data(user.binance_api_secret)
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret
        })
        order = exchange.create_market_order(symbol, side, amount)
        return order
    except Exception as e:
        return {"error": str(e)}

# 💹 تنفيذ المراجحة بين Binance و KuCoin (مثال تبسيطي)
def arbitrage_trade(user: User, symbol: str, amount: float):
    try:
        # فك التشفير
        binance_key = decrypt_data(user.binance_api_key)
        binance_secret = decrypt_data(user.binance_api_secret)
        kucoin_key = decrypt_data(user.kucoin_api_key)
        kucoin_secret = decrypt_data(user.kucoin_api_secret)

        binance = ccxt.binance({'apiKey': binance_key, 'secret': binance_secret})
        kucoin = ccxt.kucoin({'apiKey': kucoin_key, 'secret': kucoin_secret})

        # جلب الأسعار
        binance_price = binance.fetch_ticker(symbol)['last']
        kucoin_price = kucoin.fetch_ticker(symbol)['last']

        # منطق المراجحة
        if binance_price < kucoin_price:
            # شراء من Binance وبيع في KuCoin
            binance.create_market_buy_order(symbol, amount)
            kucoin.create_market_sell_order(symbol, amount)
            profit = (kucoin_price - binance_price) * amount
        else:
            # شراء من KuCoin وبيع في Binance
            kucoin.create_market_buy_order(symbol, amount)
            binance.create_market_sell_order(symbol, amount)
            profit = (binance_price - kucoin_price) * amount

        # تحديث الرصيد
        user.balance += profit
        return {"status": "success", "profit": profit}
    except Exception as e:
        return {"error": str(e)}
