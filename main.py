# -*- coding: utf-8 -*-
# import necessary libraries
import os
import asyncio
import logging
import json
from datetime import datetime, timedelta

# Import aiogram for Telegram bot functionality
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Import SQLAlchemy for database management
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Import ccxt for unified crypto exchange API
import ccxt

# Import cryptography for secure API key management
from cryptography.fernet import Fernet
import openai

# Set up logging for better debugging
# The original format had a typo, '%(message.md)s', which caused a KeyError.
# This line is corrected to use the standard message format '%(message)s'.
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- 1. Environment Variables Configuration ---
# Ensure all required environment variables are set.
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")  # A key for encrypting API keys

# Check for required environment variables
if not all([BOT_TOKEN, DATABASE_URL, OPENAI_API_KEY, ENCRYPTION_KEY]):
    raise Exception("❌ Missing one or more environment variables. Ensure BOT_TOKEN, DATABASE_URL, OPENAI_API_KEY, and ENCRYPTION_KEY are set.")

openai.api_key = OPENAI_API_KEY

# Initialize the Fernet encryption suite
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

# Initialize the Bot and Dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- 2. Database Setup and Models ---
# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    # Encrypted API keys
    api_keys = Column(String(500), default="{}")
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")
    profit_share_owed = Column(Float, default=0.0)  # Amount owed to the bot
    max_daily_loss = Column(Float, default=0.0)
    current_daily_loss = Column(Float, default=0.0)
    trade_pairs = Column(String(500), default="[]")
    min_profit_percentage = Column(Float, default=0.5) # Minimum profit percentage for a trade
    
    trade_logs = relationship("TradeLog", back_populates="user")
    
    @property
    def get_api_keys(self):
        try:
            decrypted_keys = cipher_suite.decrypt(self.api_keys.encode()).decode()
            return json.loads(decrypted_keys)
        except Exception as e:
            logging.error(f"Error decrypting API keys for user {self.id}: {e}")
            return {}
            
    @get_api_keys.setter
    def set_api_keys(self, keys_dict):
        encrypted_keys = cipher_suite.encrypt(json.dumps(keys_dict).encode()).decode()
        self.api_keys = encrypted_keys

    def is_api_keys_valid(self):
        """Checks if the stored API keys can be decrypted without error."""
        try:
            self.get_api_keys
            return True
        except Exception:
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
# NOTE: If you update the database schema (e.g., by adding new columns),
# and you get an "Unknown column" error, you will need to
# manually drop the existing table from your database and restart the bot.
# This will allow SQLAlchemy to recreate the table with the new schema.
# Use a command like `DROP TABLE users;` in your database client.

# --- 3. FSM States for Conversation Flow ---
class Form(StatesGroup):
    waiting_api_key = State()
    waiting_secret_key = State()
    waiting_passphrase = State()
    waiting_platform = State()
    waiting_investment_amount = State()
    waiting_min_profit = State()
    waiting_max_daily_loss = State()
    waiting_trade_pairs = State()

# --- 4. Helper Functions ---
# Unified function to create exchange clients
def create_exchange_client(user_api_keys, platform_name):
    platform_info = user_api_keys.get(platform_name)
    if not platform_info:
        return None

    try:
        # Platforms that require a passphrase (like Kucoin, OKX, Bybit)
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

# Unified function to verify API keys
async def verify_exchange_keys(platform_name, api_key, secret_key, passphrase=None):
    try:
        # Platforms that require a passphrase (like Kucoin, OKX, Bybit)
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

# --- 5. Keyboard Layouts ---
def get_main_menu_keyboard(is_admin=False):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1️⃣ إعدادات التداول", callback_data="menu_settings"),
        InlineKeyboardButton("2️⃣ ابدأ الاستثمار", callback_data="menu_start_invest"),
        InlineKeyboardButton("3️⃣ كشف حساب", callback_data="menu_report"),
        InlineKeyboardButton("4️⃣ حالة السوق", callback_data="menu_market_status"),
        InlineKeyboardButton("5️⃣ إيقاف الاستثمار", callback_data="menu_stop_invest"),
    )
    if is_admin:
        kb.add(InlineKeyboardButton("⚙️ لوحة تحكم المدير", callback_data="menu_admin_panel"))
    return kb

def get_settings_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=2)
    # Add a reset button if API keys are corrupted
    if not user.is_api_keys_valid():
        kb.add(InlineKeyboardButton("⚠️ إعادة ضبط مفاتيح API", callback_data="settings_reset_api_keys"))

    kb.add(
        InlineKeyboardButton("ربط/تعديل مفاتيح API", callback_data="settings_api_keys"),
        InlineKeyboardButton("تحديد مبلغ الاستثمار", callback_data="settings_investment_amount"),
        InlineKeyboardButton("تفعيل/إيقاف المنصات", callback_data="settings_toggle_platforms"),
        InlineKeyboardButton("تحديد أزواج العملات", callback_data="settings_trade_pairs"),
        InlineKeyboardButton("الحد الأدنى للربح", callback_data="settings_min_profit"),
        InlineKeyboardButton("الحد الأقصى للخسارة", callback_data="settings_max_loss"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")
    )
    return kb

def get_platforms_keyboard(user: User):
    kb = InlineKeyboardMarkup(row_width=2)
    # The list of all supported platforms
    platforms = ['binance', 'kucoin', 'okx', 'bybit', 'gateio']
    user_keys = user.get_api_keys
    for platform in platforms:
        status_text = "✅" if user_keys.get(platform, {}).get('active', False) else "❌"
        link_status = "(مربوط)" if platform in user_keys else "(غير مربوط)"
        kb.add(InlineKeyboardButton(f"{status_text} {platform.capitalize()} {link_status}", callback_data=f"toggle_platform_{platform}"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
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
    await message.answer("أهلاً بك في بوت المراجحة، اختر من القائمة:", reply_markup=get_main_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def back_to_main(call: types.CallbackQuery):
    await call.answer()
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    await call.message.edit_text("القائمة الرئيسية:", reply_markup=get_main_menu_keyboard(user))


@dp.callback_query_handler(lambda c: c.data == "menu_settings")
async def show_settings_menu(call: types.CallbackQuery):
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    await call.answer()
    await call.message.edit_text("إعدادات البوت:", reply_markup=get_settings_keyboard(user))

@dp.callback_query_handler(lambda c: c.data == "settings_api_keys")
async def handle_api_keys_menu(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    await call.message.edit_text(
        "اختر المنصة لإضافة/تعديل مفاتيح API:",
        reply_markup=get_platforms_keyboard(user)
    )
    await state.set_state(Form.waiting_platform)

@dp.callback_query_handler(lambda c: c.data.startswith("toggle_platform_"))
async def toggle_platform_status(call: types.CallbackQuery):
    platform_name = call.data.split("_")[2]
    await call.answer()
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
        user_keys = user.get_api_keys
        
        # Check if platform keys are linked
        if platform_name not in user_keys:
            await call.message.answer(f"❌ لم يتم ربط مفاتيح API لمنصة {platform_name.capitalize()} بعد.")
            return

        # Toggle the 'active' status
        user_keys[platform_name]['active'] = not user_keys[platform_name].get('active', False)
        user.set_api_keys = user_keys
        db.commit()
        
        status_text = "مفعلة" if user_keys[platform_name]['active'] else "غير مفعلة"
        await call.message.edit_text(f"✅ تم تغيير حالة منصة {platform_name.capitalize()} إلى {status_text}.",
                                      reply_markup=get_settings_keyboard(user))

@dp.callback_query_handler(lambda c: c.data == "settings_reset_api_keys")
async def reset_api_keys_handler(call: types.CallbackQuery):
    await call.answer()
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
        user.set_api_keys = {}
        db.commit()
    await call.message.edit_text("✅ تم إعادة ضبط مفاتيح API الخاصة بك. يمكنك الآن ربط المفاتيح مرة أخرى من القائمة الرئيسية.", reply_markup=get_main_menu_keyboard())


@dp.callback_query_handler(lambda c: c.data.startswith("platform_"), state=Form.waiting_platform)
async def platform_selected_for_api_keys(call: types.CallbackQuery, state: FSMContext):
    platform_name = call.data.split("_")[1]
    await state.update_data(platform=platform_name)
    await call.answer()
    
    # Check for platforms that require a passphrase
    if platform_name in ['kucoin', 'okx', 'bybit']:
        await call.message.edit_text(f"أرسل مفتاح API الخاص بمنصة {platform_name.capitalize()}:")
        await state.set_state(Form.waiting_api_key)
    else:
        await call.message.edit_text(f"أرسل مفتاح API الخاص بمنصة {platform_name.capitalize()}:")
        await state.set_state(Form.waiting_api_key)

@dp.message_handler(state=Form.waiting_api_key)
async def api_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform_name = data.get("platform")
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)

    await message.answer("أرسل الـ Secret Key:")
    await state.set_state(Form.waiting_secret_key)

@dp.message_handler(state=Form.waiting_secret_key)
async def secret_key_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform_name = data.get("platform")
    secret_key = message.text.strip()
    await state.update_data(secret_key=secret_key)

    if platform_name in ['kucoin', 'okx', 'bybit']:
        await message.answer(f"أرسل الـ Passphrase الخاص بـ {platform_name.capitalize()}:")
        await state.set_state(Form.waiting_passphrase)
    else:
        is_valid = await verify_exchange_keys(platform_name, data.get("api_key"), secret_key)
        if not is_valid:
            await message.answer("❌ المفاتيح غير صحيحة أو لا تحتوي على الصلاحيات اللازمة.\nتأكد من تفعيل صلاحيات القراءة والتداول فقط، وأعد المحاولة.")
            await state.finish()
            return
        
        with SessionLocal() as db:
            user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
            user_keys = user.get_api_keys
            user_keys[platform_name] = {'key': data.get("api_key"), 'secret': secret_key, 'active': True}
            user.set_api_keys = user_keys
            db.commit()
            
        await message.answer(f"✅ تم ربط {platform_name.capitalize()} بنجاح!")
        await state.finish()
        await message.answer("العودة للقائمة الرئيسية:", reply_markup=get_main_menu_keyboard())

@dp.message_handler(state=Form.waiting_passphrase)
async def passphrase_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    passphrase = message.text.strip()
    platform_name = data.get("platform")

    is_valid = await verify_exchange_keys(platform_name, data.get("api_key"), data.get("secret_key"), passphrase)
    if not is_valid:
        await message.answer("❌ المفاتيح غير صحيحة أو لا تحتوي على الصلاحيات اللازمة.\nتأكد من تفعيل صلاحيات القراءة والتداول فقط، وأعد المحاولة.")
        await state.finish()
        return

    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user_keys = user.get_api_keys
        user_keys[platform_name] = {'key': data.get("api_key"), 'secret': data.get("secret_key"), 'passphrase': passphrase, 'active': True}
        user.set_api_keys = user_keys
        db.commit()
        
    await message.answer(f"✅ تم ربط {platform_name.capitalize()} بنجاح!")
    await state.finish()
    await message.answer("العودة للقائمة الرئيسية:", reply_markup=get_main_menu_keyboard())


# --- 7. Arbitrage Loop Logic ---
async def run_arbitrage_loop(user_telegram_id, bot: Bot):
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
        if not user or user.investment_status != "started":
            return

    while True:
        with SessionLocal() as db:
            user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
            if not user or user.investment_status != "started":
                return
            
            # Check for max daily loss
            if user.max_daily_loss > 0 and user.current_daily_loss >= user.max_daily_loss:
                user.investment_status = "stopped"
                db.commit()
                await bot.send_message(user_telegram_id, "🛑 تم إيقاف الاستثمار تلقائيًا بسبب الوصول إلى الحد الأقصى للخسارة اليومية.")
                return

            user_keys = user.get_api_keys
            # Check if API keys are valid before proceeding
            if not user.is_api_keys_valid():
                user.investment_status = "stopped"
                db.commit()
                await bot.send_message(user_telegram_id, "❌ تم إيقاف الاستثمار بسبب وجود خطأ في مفاتيح API. يرجى إعادة ضبطها من قائمة الإعدادات.")
                return

            available_platforms = [p for p, k in user_keys.items() if k.get('active')]
            
            # Skip if less than two platforms are active
            if len(available_platforms) < 2:
                await bot.send_message(user_telegram_id, "❌ يجب تفعيل منصتين على الأقل للاستثمار.")
                user.investment_status = "stopped"
                db.commit()
                continue
                
            try:
                # Find arbitrage opportunities for each pair
                for trade_pair in json.loads(user.trade_pairs):
                    prices = {}
                    for platform_name in available_platforms:
                        exchange_client = create_exchange_client(user_keys, platform_name)
                        if exchange_client:
                            try:
                                ticker = await exchange_client.fetch_ticker(trade_pair)
                                prices[platform_name] = ticker
                            except Exception as e:
                                logging.error(f"Could not fetch ticker from {platform_name}: {e}")

                    if len(prices) < 2:
                        continue # Cannot perform arbitrage with less than 2 prices
                    
                    # Find the best buy and sell prices
                    best_buy_platform = min(prices, key=lambda p: prices[p]['ask'])
                    best_sell_platform = max(prices, key=lambda p: prices[p]['bid'])
                    
                    buy_price = prices[best_buy_platform]['ask']
                    sell_price = prices[best_sell_platform]['bid']
                    
                    profit_percentage = ((sell_price - buy_price) / buy_price) * 100
                    
                    if profit_percentage > user.min_profit_percentage:
                        # --- Execute Trade Logic ---
                        # Fetch user's available USDT balance on the buy platform
                        buy_exchange_client = create_exchange_client(user_keys, best_buy_platform)
                        if not buy_exchange_client: continue
                        balance = await buy_exchange_client.fetch_balance()
                        available_balance = balance['total']['USDT']
                        
                        amount_to_trade = min(user.investment_amount, available_balance)
                        if amount_to_trade > 0:
                            # Perform the market buy and sell orders
                            try:
                                buy_order = await buy_exchange_client.create_market_buy_order(trade_pair, amount_to_trade / buy_price)
                                # A small delay to ensure buy order is registered
                                await asyncio.sleep(0.5)
                                sell_exchange_client = create_exchange_client(user_keys, best_sell_platform)
                                if not sell_exchange_client: continue
                                sell_order = await sell_exchange_client.create_market_sell_order(trade_pair, buy_order['amount'])

                                # Calculate actual profit based on executed prices
                                actual_profit = (sell_order['cost'] - buy_order['cost'])
                                bot_share = actual_profit * (10 / 100) # 10% profit share
                                user_profit = actual_profit - bot_share
                                
                                # Log trade and update user stats
                                user.profit_share_owed += bot_share
                                trade_log = TradeLog(
                                    user_id=user.id,
                                    trade_type=f"Buy {best_buy_platform.capitalize()} / Sell {best_sell_platform.capitalize()}",
                                    amount=buy_order['amount'],
                                    profit=user_profit
                                )
                                db.add(trade_log)
                                db.commit()
                                await bot.send_message(user_telegram_id, f"✅ تمت صفقة مراجحة ناجحة على {trade_pair}!\nالربح الصافي: {user_profit:.2f} USDT")
                            except Exception as trade_e:
                                logging.error(f"Error executing trade for user {user.id}: {trade_e}")
                                # Handle failed trades
                                pass # In a real bot, you'd add more sophisticated error recovery here

            except Exception as e:
                logging.error(f"Error in arbitrage loop for user {user.id}: {e}")
                
        await asyncio.sleep(60) # Sleep for a minute before the next loop

# --- 8. OpenAI Market Analysis ---
async def get_market_analysis():
    # Use a real-time price fetcher for better accuracy
    # For now, we'll rely on a basic prompt.
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful crypto market analyst."},
                {"role": "user", "content": (
                    "اعطني ملخص تحليل سوق العملات الرقمية الحالي، مع أسعار بعض العملات الرئيسية مثل BTC و ETH,"
                    " ونبذة عن توقعات السوق بناء على مؤشرات تقنية مثل RSI و MACD."
                    " اذكر التحذيرات إن وجدت."
                )}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ خطأ في جلب تحليل السوق من OpenAI: {str(e)}"

@dp.callback_query_handler(lambda c: c.data == "menu_market_status")
async def market_status_handler(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("⏳ جاري تحليل السوق، يرجى الانتظار...")
    analysis_text = await get_market_analysis()
    await call.message.edit_text(analysis_text, reply_markup=get_main_menu_keyboard())


# --- 9. Bot Entry Point ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
