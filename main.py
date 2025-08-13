# -*- coding: utf-8 -*-
import os
import asyncio
import logging
import json
from datetime import datetime

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

import ccxt.async_support as ccxt
from cryptography.fernet import Fernet, InvalidToken
from openai import OpenAI

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- 1. متغيرات البيئة ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not all([BOT_TOKEN, DATABASE_URL, OPENAI_API_KEY, ENCRYPTION_KEY]):
    raise Exception("❌ Missing one or more environment variables.")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- 2. قاعدة البيانات ---
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    api_keys = Column(String(500), default="{}")
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")
    profit_share_owed = Column(Float, default=0.0)
    max_daily_loss = Column(Float, default=0.0)
    current_daily_loss = Column(Float, default=0.0)
    trade_pairs = Column(String(500), default="[]")
    min_profit_percentage = Column(Float, default=0.5)
    trade_logs = relationship("TradeLog", back_populates="user")
    
    @property
    def get_api_keys(self):
        try:
            decrypted_keys = cipher_suite.decrypt(self.api_keys.encode()).decode()
            return json.loads(decrypted_keys)
        except:
            return {}

    @get_api_keys.setter
    def set_api_keys(self, keys_dict):
        self.api_keys = cipher_suite.encrypt(json.dumps(keys_dict).encode()).decode()

    def is_api_keys_valid(self):
        try:
            self.get_api_keys
            return True
        except:
            return False

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    trade_type = Column(String(50))
    amount = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="trade_logs")

Base.metadata.create_all(engine)

# --- 3. FSM ---
class Form(StatesGroup):
    waiting_api_key = State()
    waiting_secret_key = State()
    waiting_passphrase = State()
    waiting_platform = State()

# --- 4. Helper Functions ---
async def create_exchange_client(user_api_keys, platform_name):
    platform_info = user_api_keys.get(platform_name)
    if not platform_info:
        return None
    try:
        if platform_name in ['kucoin', 'okx', 'bybit'] and 'passphrase' in platform_info:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': platform_info['key'],
                'secret': platform_info['secret'],
                'password': platform_info['passphrase'],
            })
        else:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': platform_info['key'],
                'secret': platform_info['secret'],
            })
        return exchange
    except Exception as e:
        logging.error(f"Error creating client for {platform_name}: {e}")
        return None

async def verify_exchange_keys(platform_name, api_key, secret_key, passphrase=None):
    exchange = None
    try:
        if platform_name in ['kucoin', 'okx', 'bybit'] and passphrase:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': api_key,
                'secret': secret_key,
                'password': passphrase,
            })
        else:
            exchange = getattr(ccxt, platform_name)({
                'apiKey': api_key,
                'secret': secret_key,
            })
        await exchange.load_markets()
        return True
    except Exception as e:
        logging.error(f"Failed to verify {platform_name} keys: {e}")
        return False
    finally:
        if exchange:
            await exchange.close()

# --- 5. Keyboards ---
def get_main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("إعدادات التداول", callback_data="menu_settings"),
        InlineKeyboardButton("ابدأ الاستثمار", callback_data="menu_start_invest"),
        InlineKeyboardButton("كشف حساب", callback_data="menu_report"),
        InlineKeyboardButton("حالة السوق", callback_data="menu_market_status"),
        InlineKeyboardButton("إيقاف الاستثمار", callback_data="menu_stop_invest")
    )
    return kb

def get_platforms_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=2)
    platforms = ['binance','kucoin','okx','bybit','gateio']
    user_keys = user.get_api_keys
    for platform in platforms:
        status = "✅" if user_keys.get(platform, {}).get('active') else "❌"
        kb.add(InlineKeyboardButton(f"{status} {platform.capitalize()}", callback_data=f"platform_{platform}"))
    kb.add(InlineKeyboardButton("رجوع", callback_data="main_menu"))
    return kb

# --- 6. Handlers ---
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = User(telegram_id=message.from_user.id)
            db.add(user)
            db.commit()
        if not user.is_api_keys_valid():
            user.set_api_keys = {}
            db.commit()
            await message.answer("⚠️ تم إعادة ضبط مفاتيح API تلقائيًا.")
    await message.answer("أهلاً بك في بوت المراجحة", reply_markup=get_main_menu_keyboard())

# --- 7. ربط مفاتيح API ---
@dp.callback_query_handler(lambda c: c.data.startswith("platform_"), state=Form.waiting_platform)
async def platform_selected_for_api_keys(call: types.CallbackQuery, state: FSMContext):
    platform_name = call.data.split("_")[1]
    await state.update_data(platform=platform_name)
    await call.message.edit_text(f"أرسل مفتاح API الخاص بـ {platform_name.capitalize()}:")
    await state.set_state(Form.waiting_api_key)
    await call.answer()

@dp.message_handler(state=Form.waiting_api_key)
async def api_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(api_key=message.text.strip())
    await message.answer("أرسل الـ Secret Key:")
    await state.set_state(Form.waiting_secret_key)

@dp.message_handler(state=Form.waiting_secret_key)
async def secret_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    api_key = data.get("api_key")
    secret_key = message.text.strip()
    platform_name = data.get("platform")
    passphrase = None
    if platform_name in ['kucoin','okx','bybit']:
        await state.update_data(secret_key=secret_key)
        await message.answer("أرسل الـ Passphrase:")
        await state.set_state(Form.waiting_passphrase)
        return
    valid = await verify_exchange_keys(platform_name, api_key, secret_key)
    if not valid:
        await message.answer("❌ المفاتيح غير صحيحة.")
        await state.finish()
        return
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        keys = user.get_api_keys
        keys[platform_name] = {'key': api_key,'secret': secret_key,'active':True}
        user.set_api_keys = keys
        db.commit()
    await message.answer(f"✅ تم ربط {platform_name.capitalize()} بنجاح!")
    await state.finish()
    await message.answer("العودة للقائمة الرئيسية:", reply_markup=get_main_menu_keyboard())

@dp.message_handler(state=Form.waiting_passphrase)
async def passphrase_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    api_key = data.get("api_key")
    secret_key = data.get("secret_key")
    passphrase = message.text.strip()
    platform_name = data.get("platform")
    valid = await verify_exchange_keys(platform_name, api_key, secret_key, passphrase)
    if not valid:
        await message.answer("❌ المفاتيح غير صحيحة.")
        await state.finish()
        return
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        keys = user.get_api_keys
        keys[platform_name] = {'key': api_key,'secret': secret_key,'passphrase':passphrase,'active':True}
        user.set_api_keys = keys
        db.commit()
    await message.answer(f"✅ تم ربط {platform_name.capitalize()} بنجاح!")
    await state.finish()
    await message.answer("العودة للقائمة الرئيسية:", reply_markup=get_main_menu_keyboard())

# --- 8. حلقة المراجحة ---
async def run_arbitrage_loop(user_telegram_id, bot: Bot):
    while True:
        with SessionLocal() as db:
            user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
            if not user or user.investment_status != "started":
                return
            if not user.is_api_keys_valid():
                user.investment_status = "stopped"
                db.commit()
                await bot.send_message(user_telegram_id,"❌ تم إيقاف الاستثمار بسبب خطأ في مفاتيح API.")
                return
            user_keys = user.get_api_keys
            platforms = [p for p,k in user_keys.items() if k.get('active')]
            if len(platforms)<2:
                await bot.send_message(user_telegram_id,"❌ يجب تفعيل منصتين على الأقل.")
                user.investment_status="stopped"
                db.commit()
                continue
        await asyncio.sleep(60)  # انتظار قبل الجولة القادمة

# --- 9. OpenAI Market Analysis ---
async def get_market_analysis():
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You are a helpful crypto analyst."},
                {"role":"user","content":"اعطني ملخص سوق العملات الرقمية مع BTC و ETH وتحليل تقني."}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ خطأ في تحليل السوق: {str(e)}"

@dp.callback_query_handler(lambda c: c.data=="menu_market_status")
async def market_status_handler(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("⏳ جاري تحليل السوق...")
    analysis = await get_market_analysis()
    await call.message.edit_text(analysis, reply_markup=get_main_menu_keyboard())

# --- 10. تشغيل البوت ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
