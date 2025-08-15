import os
import asyncio
import ccxt.async_support as ccxt
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from sqlalchemy import create_engine, Column, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet

# ---------------- قاعدة البيانات ----------------
Base = declarative_base()

class UserPlatform(Base):
    __tablename__ = "user_platforms"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    platform_name = Column(String(50), nullable=False)
    api_key = Column(String(255), nullable=False)
    api_secret = Column(String(255), nullable=False)
    passphrase = Column(String(255), nullable=True)
    trade_amount = Column(String(50), nullable=False)  # المبلغ المستخدم

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

# ---------------- تشفير ----------------
FERNET_KEY = os.getenv("FERNET_KEY").encode()
fernet = Fernet(FERNET_KEY)

def encrypt_value(value: str):
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(value: str):
    return fernet.decrypt(value.encode()).decode()

# ---------------- إعداد البوت ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ---------------- تهيئة المنصات ----------------
async def init_user_platforms(user_id):
    session = SessionLocal()
    platforms = session.query(UserPlatform).filter_by(telegram_id=user_id).all()
    active_exchanges = {}
    
    for plat in platforms:
        try:
            api_key = decrypt_value(plat.api_key)
            api_secret = decrypt_value(plat.api_secret)
            passphrase = decrypt_value(plat.passphrase) if plat.passphrase else None

            if plat.platform_name.lower() == "kucoin":
                exchange = ccxt.kucoin({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'password': passphrase,
                    'enableRateLimit': True,
                })
                fee = 0.001  # مثال رسوم 0.1%
            elif plat.platform_name.lower() == "binance":
                exchange = ccxt.binance({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                })
                fee = 0.001
            elif plat.platform_name.lower() == "bitget":
                exchange = ccxt.bitget({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'password': passphrase,
                    'enableRateLimit': True,
                })
                fee = 0.001
            else:
                continue

            await exchange.fetch_balance()
            active_exchanges[plat.platform_name] = {
                "exchange": exchange,
                "amount": float(plat.trade_amount),
                "fee": fee
            }
            print(f"[INFO] User {user_id} platform {plat.platform_name} initialized.")
        except Exception as e:
            print(f"[ERROR] Failed to init {plat.platform_name} user {user_id}: {e}")

    session.close()
    return active_exchanges

# ---------------- إغلاق المنصات ----------------
async def close_exchanges(exchanges):
    for info in exchanges.values():
        try:
            await info["exchange"].close()
        except Exception as e:
            print(f"[WARNING] Error closing exchange: {e}")

# ---------------- المراجحة الفعلية ----------------
async def triangular_arbitrage(user_id):
    exchanges = await init_user_platforms(user_id)

    for name, info in exchanges.items():
        exchange = info["exchange"]
        amount = info["amount"]
        fee = info["fee"]
        try:
            tickers = await exchange.fetch_tickers()
            symbols = list(tickers.keys())
            for s1 in symbols:
                for s2 in symbols:
                    for s3 in symbols:
                        try:
                            # تحقق من مثلث متوافق
                            if s1.split("/")[1] == s2.split("/")[0] and s2.split("/")[1] == s3.split("/")[0] and s3.split("/")[1] == s1.split("/")[0]:
                                price1 = tickers[s1]['ask']
                                price2 = tickers[s2]['ask']
                                price3 = tickers[s3]['bid']

                                # ربح بعد الرسوم
                                net_profit = ((1 / price1 * (1 - fee)) * price2 * (1 - fee) * price3 * (1 - fee)) - 1

                                if net_profit > 0:
                                    msg = (
                                        f"💰 Triangular Arbitrage Opportunity!\n"
                                        f"Platform: {name}\n"
                                        f"Pairs: {s1} → {s2} → {s3}\n"
                                        f"Amount: {amount}\n"
                                        f"Net Profit: {net_profit*100:.2f}%"
                                    )
                                    await bot.send_message(user_id, msg)

                                    # تنفيذ الصفقات
                                    qty1 = amount
                                    qty2 = qty1 / price1
                                    qty3 = qty2 * price2

                                    await exchange.create_market_buy_order(s1, qty1)
                                    await exchange.create_market_buy_order(s2, qty2)
                                    await exchange.create_market_sell_order(s3, qty3)

                        except Exception:
                            continue
        except Exception as e:
            print(f"[ERROR] {name} arbitrage scan failed: {e}")

    await close_exchanges(exchanges)

# ---------------- أوامر البوت ----------------
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("🤖 مرحبًا! البوت جاهز للتداول والمراجحة التلقائية.")

@dp.message_handler(commands=["scan"])
async def cmd_scan(message: types.Message):
    await message.reply("🔎 جاري البحث عن فرص المراجحة الثلاثية...")
    await triangular_arbitrage(message.from_user.id)

# ---------------- تشغيل البوت ----------------
if __name__ == "__main__":
    start_polling(dp, skip_updates=True)
