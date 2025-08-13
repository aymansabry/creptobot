# -*- coding: utf-8 -*-
import os
import asyncio
import logging
import json
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor  # ✅ التصحيح هنا
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# النسخة غير المتزامنة من ccxt
import ccxt.async_support as ccxt

from cryptography.fernet import Fernet, InvalidToken
from openai import OpenAI

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- 1) المتغيرات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not all([BOT_TOKEN, DATABASE_URL, OPENAI_API_KEY, ENCRYPTION_KEY]):
    raise Exception("❌ Missing environment variables.")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# مفتاح التشفير لازم يكون Base64 urlsafe بطول 32 بايت
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- 2) قاعدة البيانات ---
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    api_keys = Column(String(500), default="{}")  # مخزنة مشفرة
    investment_amount = Column(Float, default=0.0)
    investment_status = Column(String(20), default="stopped")  # "started" | "stopped"
    profit_share_owed = Column(Float, default=0.0)
    max_daily_loss = Column(Float, default=0.0)
    current_daily_loss = Column(Float, default=0.0)
    trade_pairs = Column(String(500), default="[]")  # JSON list
    min_profit_percentage = Column(Float, default=0.5)

    trade_logs = relationship("TradeLog", back_populates="user")

    # ✅ اسم واضح للـ property + setter سليم
    @property
    def api_keys_dict(self) -> dict:
        try:
            decrypted = cipher_suite.decrypt(self.api_keys.encode()).decode()
            return json.loads(decrypted)
        except (InvalidToken, json.JSONDecodeError, UnicodeDecodeError):
            return {}

    @api_keys_dict.setter
    def api_keys_dict(self, keys_dict: dict):
        payload = json.dumps(keys_dict).encode()
        encrypted = cipher_suite.encrypt(payload).decode()
        self.api_keys = encrypted

    def is_api_keys_valid(self) -> bool:
        try:
            # محاولة فك + تحويل JSON فعلية
            decrypted = cipher_suite.decrypt(self.api_keys.encode()).decode()
            json.loads(decrypted)
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

# --- 3) FSM ---
class Form(StatesGroup):
    waiting_api_key = State()
    waiting_secret_key = State()
    waiting_passphrase = State()
    waiting_platform = State()
    waiting_investment_amount = State()
    waiting_min_profit = State()
    waiting_max_daily_loss = State()
    waiting_trade_pairs = State()

# --- 4) Keyboards ---
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

def get_settings_keyboard(user: 'User'):
    kb = InlineKeyboardMarkup(row_width=2)
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

def get_platforms_keyboard(user: 'User'):
    kb = InlineKeyboardMarkup(row_width=2)
    platforms = ['binance', 'kucoin', 'okx', 'bybit', 'gateio']
    user_keys = user.api_keys_dict  # ✅
    for platform in platforms:
        status_text = "✅" if user_keys.get(platform, {}).get('active', False) else "❌"
        link_status = "(مربوط)" if platform in user_keys else "(غير مربوط)"
        kb.add(InlineKeyboardButton(f"{status_text} {platform.capitalize()} {link_status}", callback_data=f"toggle_platform_{platform}"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="menu_settings"))
    return kb

def get_link_platforms_keyboard(user: 'User'):
    kb = InlineKeyboardMarkup(row_width=2)
    platforms = ['binance', 'kucoin', 'okx', 'bybit', 'gateio']
    for platform in platforms:
        kb.add(InlineKeyboardButton(platform.capitalize(), callback_data=f"platform_{platform}"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="menu_settings"))
    return kb

# --- 5) CCXT Helpers ---
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
        await exchange.load_markets()
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
        await asyncio.wait_for(exchange.load_markets(), timeout=10)
        return True
    except Exception as e:
        logging.error(f"Failed to verify {platform_name} keys: {e}")
        return False
    finally:
        if exchange:
            try:
                await exchange.close()
            except Exception:
                pass

# --- 6) Handlers: Start/Main Menu ---
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = User(telegram_id=message.from_user.id)
            db.add(user)
            db.commit()
        # إصلاح أي مفاتيح تالفة
        if not user.is_api_keys_valid():
            user.api_keys_dict = {}  # ✅
            db.commit()
            await message.answer("⚠️ تم إعادة ضبط مفاتيح API تلقائيًا.")
    await message.answer("أهلاً بك في بوت المراجحة، اختر من القائمة:", reply_markup=get_main_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def back_to_main(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("القائمة الرئيسية:", reply_markup=get_main_menu_keyboard())

# --- 7) Settings Menu ---
@dp.callback_query_handler(lambda c: c.data == "menu_settings")
async def show_settings_menu(call: types.CallbackQuery):
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    await call.answer()
    await call.message.edit_text("إعدادات البوت:", reply_markup=get_settings_keyboard(user))

# 7.1 ربط/تعديل مفاتيح API
@dp.callback_query_handler(lambda c: c.data == "settings_api_keys")
async def handle_api_keys_menu(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    await call.message.edit_text("اختر المنصة لإضافة/تعديل مفاتيح API:", reply_markup=get_link_platforms_keyboard(user))
    await state.set_state(Form.waiting_platform)

@dp.callback_query_handler(lambda c: c.data.startswith("platform_"), state=Form.waiting_platform)
async def platform_selected_for_api_keys(call: types.CallbackQuery, state: FSMContext):
    platform_name = call.data.split("_", 1)[1]
    await state.update_data(platform=platform_name)
    await call.answer()
    await call.message.edit_text(f"أرسل مفتاح API الخاص بمنصة {platform_name.capitalize()}:")
    await state.set_state(Form.waiting_api_key)

@dp.message_handler(state=Form.waiting_api_key)
async def api_key_received(message: types.Message, state: FSMContext):
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
        valid = await verify_exchange_keys(platform_name, data.get("api_key"), secret_key)
        if not valid:
            await message.answer("❌ المفاتيح غير صحيحة أو لا تحتوي على الصلاحيات اللازمة.\nتأكد من صلاحيات القراءة والتداول فقط.")
            await state.finish()
            return
        with SessionLocal() as db:
            user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
            keys = user.api_keys_dict  # ✅
            keys[platform_name] = {'key': data.get("api_key"), 'secret': secret_key, 'active': True}
            user.api_keys_dict = keys  # ✅
            db.commit()
        await message.answer(f"✅ تم ربط {platform_name.capitalize()} بنجاح!")
        await state.finish()
        with SessionLocal() as db:
            user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        await message.answer("إعدادات البوت:", reply_markup=get_settings_keyboard(user))

@dp.message_handler(state=Form.waiting_passphrase)
async def passphrase_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    platform_name = data.get("platform")
    api_key = data.get("api_key")
    secret_key = data.get("secret_key")
    passphrase = message.text.strip()

    valid = await verify_exchange_keys(platform_name, api_key, secret_key, passphrase)
    if not valid:
        await message.answer("❌ المفاتيح غير صحيحة أو لا تحتوي على الصلاحيات اللازمة.")
        await state.finish()
        return
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        keys = user.api_keys_dict  # ✅
        keys[platform_name] = {
            'key': api_key, 'secret': secret_key, 'passphrase': passphrase, 'active': True
        }
        user.api_keys_dict = keys  # ✅
        db.commit()
    await message.answer(f"✅ تم ربط {platform_name.capitalize()} بنجاح!")
    await state.finish()
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    await message.answer("إعدادات البوت:", reply_markup=get_settings_keyboard(user))

# 7.2 تفعيل/إيقاف المنصات
@dp.callback_query_handler(lambda c: c.data == "settings_toggle_platforms")
async def settings_toggle_platforms(call: types.CallbackQuery):
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
    await call.answer()
    await call.message.edit_text("تفعيل/إيقاف المنصات:", reply_markup=get_platforms_keyboard(user))

@dp.callback_query_handler(lambda c: c.data.startswith("toggle_platform_"))
async def toggle_platform_status(call: types.CallbackQuery):
    platform_name = call.data.split("_", 2)[2]
    await call.answer()
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
        user_keys = user.api_keys_dict  # ✅
        if platform_name not in user_keys:
            await call.message.answer(f"❌ لم يتم ربط مفاتيح {platform_name.capitalize()} بعد. ادخل إلى ربط/تعديل مفاتيح API أولاً.")
            return
        user_keys[platform_name]['active'] = not user_keys[platform_name].get('active', False)
        user.api_keys_dict = user_keys  # ✅
        db.commit()
        status_text = "مفعلة" if user_keys[platform_name]['active'] else "غير مفعلة"
    await call.message.edit_text(f"✅ تم تغيير حالة {platform_name.capitalize()} إلى {status_text}.", reply_markup=get_settings_keyboard(user))

# 7.3 تحديد مبلغ الاستثمار
@dp.callback_query_handler(lambda c: c.data == "settings_investment_amount")
async def settings_invest_amount(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("💰 أرسل مبلغ الاستثمار المطلوب (بالـ USDT):")
    await state.set_state(Form.waiting_investment_amount)

@dp.message_handler(state=Form.waiting_investment_amount)
async def set_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ رقم غير صالح. أعد الإرسال.")
        return
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.investment_amount = amount
        db.commit()
    await state.finish()
    await message.answer(f"✅ تم ضبط مبلغ الاستثمار: {amount} USDT", reply_markup=get_main_menu_keyboard())

# 7.4 الحد الأدنى للربح
@dp.callback_query_handler(lambda c: c.data == "settings_min_profit")
async def settings_min_profit(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("٪ أرسل الحد الأدنى لنسبة الربح (مثال 0.8):")
    await state.set_state(Form.waiting_min_profit)

@dp.message_handler(state=Form.waiting_min_profit)
async def set_min_profit(message: types.Message, state: FSMContext):
    try:
        perc = float(message.text.strip())
        if perc < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ قيمة غير صالحة. أعد الإرسال.")
        return
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.min_profit_percentage = perc
        db.commit()
    await state.finish()
    await message.answer(f"✅ تم ضبط الحد الأدنى للربح: {perc}%", reply_markup=get_main_menu_keyboard())

# 7.5 الحد الأقصى للخسارة اليومية
@dp.callback_query_handler(lambda c: c.data == "settings_max_loss")
async def settings_max_loss(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("أرسل الحد الأقصى للخسارة اليومية (قيمة USDT، مثال 25):")
    await state.set_state(Form.waiting_max_daily_loss)

@dp.message_handler(state=Form.waiting_max_daily_loss)
async def set_max_loss(message: types.Message, state: FSMContext):
    try:
        val = float(message.text.strip())
        if val < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ قيمة غير صالحة. أعد الإرسال.")
        return
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.max_daily_loss = val
        db.commit()
    await state.finish()
    await message.answer(f"✅ تم ضبط الحد الأقصى للخسارة اليومية: {val} USDT", reply_markup=get_main_menu_keyboard())

# 7.6 أزواج التداول
@dp.callback_query_handler(lambda c: c.data == "settings_trade_pairs")
async def settings_trade_pairs(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("أرسل أزواج التداول مفصولة بفواصل مثل:\nBTC/USDT,ETH/USDT,SOL/USDT")
    await state.set_state(Form.waiting_trade_pairs)

@dp.message_handler(state=Form.waiting_trade_pairs)
async def set_trade_pairs(message: types.Message, state: FSMContext):
    raw = message.text.strip()
    pairs = [p.strip().upper() for p in raw.split(",") if p.strip()]
    if not pairs:
        await message.answer("❌ صيغة غير صالحة. أعد الإرسال.")
        return
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
        user.trade_pairs = json.dumps(pairs)
        db.commit()
    await state.finish()
    await message.answer(f"✅ تم ضبط الأزواج: {', '.join(pairs)}", reply_markup=get_main_menu_keyboard())

# --- 8) بدء/إيقاف الاستثمار + حلقة المراجحة ---
# مُعرّف مهام الخلفية لكل مستخدم
user_tasks = {}

async def run_arbitrage_loop(user_telegram_id: int):
    logging.info(f"[loop] start for user {user_telegram_id}")
    while True:
        await asyncio.sleep(1)  # تجنب الدوران السريع
        with SessionLocal() as db:
            user = db.query(User).filter_by(telegram_id=user_telegram_id).first()
            if not user or user.investment_status != "started":
                logging.info(f"[loop] stop for user {user_telegram_id}")
                return

            # وقف تلقائي في حال خطأ بالمفاتيح
            if not user.is_api_keys_valid():
                user.investment_status = "stopped"
                db.commit()
                await bot.send_message(user_telegram_id, "❌ تم إيقاف الاستثمار بسبب خطأ في مفاتيح API.")
                return

            keys = user.api_keys_dict  # ✅
            active_platforms = [p for p, k in keys.items() if k.get('active')]
            if len(active_platforms) < 2:
                await bot.send_message(user_telegram_id, "⚠️ يجب تفعيل منصتين على الأقل.")
                user.investment_status = "stopped"
                db.commit()
                continue

            # قراءة الأزواج
            try:
                pairs = json.loads(user.trade_pairs) if user.trade_pairs else []
            except Exception:
                pairs = []

            if not pairs:
                await bot.send_message(user_telegram_id, "⚠️ لا توجد أزواج تداول محددة. أضفها من الإعدادات.")
                user.investment_status = "stopped"
                db.commit()
                continue

            # نموذج مبسّط لجلب أسعار من منصتين ومحاولة تقييم فرصة (بدون تنفيذ أوامر فعلية)
            try:
                for pair in pairs:
                    prices = {}
                    for plat in active_platforms:
                        exchange = None
                        try:
                            creds = keys.get(plat, {})
                            if not creds:
                                continue
                            if plat in ['kucoin', 'okx', 'bybit'] and 'passphrase' in creds:
                                exchange = getattr(ccxt, plat)({
                                    'apiKey': creds['key'],
                                    'secret': creds['secret'],
                                    'password': creds['passphrase'],
                                })
                            else:
                                exchange = getattr(ccxt, plat)({
                                    'apiKey': creds['key'],
                                    'secret': creds['secret'],
                                })
                            ticker = await asyncio.wait_for(exchange.fetch_ticker(pair), timeout=8)
                            # حفظ bid/ask فقط
                            prices[plat] = {'bid': ticker.get('bid'), 'ask': ticker.get('ask')}
                        except Exception as e:
                            logging.error(f"[loop] fetch ticker error {plat} {pair}: {e}")
                        finally:
                            if exchange:
                                try:
                                    await exchange.close()
                                except Exception:
                                    pass

                    # لو عندي منصتين على الأقل فيها سعر
                    valid = {p: t for p, t in prices.items() if t.get('bid') and t.get('ask')}
                    if len(valid) < 2:
                        continue

                    best_buy = min(valid.items(), key=lambda x: x[1]['ask'])
                    best_sell = max(valid.items(), key=lambda x: x[1]['bid'])
                    buy_price = best_buy[1]['ask']
                    sell_price = best_sell[1]['bid']

                    if buy_price and sell_price and buy_price > 0:
                        profit_pct = ((sell_price - buy_price) / buy_price) * 100
                        if profit_pct >= user.min_profit_percentage:
                            # هنا مكان تنفيذ الأوامر الفعلية لو أردت (معلّق حفاظًا على الأمان)
                            await bot.send_message(
                                user_telegram_id,
                                f"💡 احتمال مراجحة على {pair} | شراء من {best_buy[0].capitalize()} بسعر {buy_price}, بيع في {best_sell[0].capitalize()} بسعر {sell_price} | ربح تقديري ~ {profit_pct:.2f}%"
                            )

            except Exception as e:
                logging.error(f"[loop] unexpected error user {user_telegram_id}: {e}")

@dp.callback_query_handler(lambda c: c.data == "menu_start_invest")
async def start_invest(call: types.CallbackQuery):
    await call.answer()
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
        if not user:
            await call.message.answer("❌ مستخدم غير معروف. أرسل /start.")
            return
        user.investment_status = "started"
        db.commit()

    # شغّل التاسك لو مش شغالة
    if call.from_user.id not in user_tasks or user_tasks[call.from_user.id].done():
        user_tasks[call.from_user.id] = asyncio.create_task(run_arbitrage_loop(call.from_user.id))

    await call.message.edit_text("✅ تم بدء الاستثمار.", reply_markup=get_main_menu_keyboard())

@dp.callback_query_handler(lambda c: c.data == "menu_stop_invest")
async def stop_invest(call: types.CallbackQuery):
    await call.answer()
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
        if user:
            user.investment_status = "stopped"
            db.commit()
    await call.message.edit_text("🛑 تم إيقاف الاستثمار.", reply_markup=get_main_menu_keyboard())

# --- 9) كشف الحساب المبسّط ---
@dp.callback_query_handler(lambda c: c.data == "menu_report")
async def report_handler(call: types.CallbackQuery):
    await call.answer()
    with SessionLocal() as db:
        user = db.query(User).filter_by(telegram_id=call.from_user.id).first()
        if not user:
            await call.message.edit_text("❌ مستخدم غير معروف. أرسل /start.", reply_markup=get_main_menu_keyboard())
            return
        trades_count = db.query(TradeLog).filter_by(user_id=user.id).count()
        total_profit = db.query(TradeLog).filter_by(user_id=user.id).with_entities(TradeLog.profit).all()
        total_profit_val = sum([p[0] or 0.0 for p in total_profit]) if total_profit else 0.0

        txt = (
            f"📄 كشف حساب:\n"
            f"- حالة الاستثمار: {user.investment_status}\n"
            f"- مبلغ الاستثمار: {user.investment_amount} USDT\n"
            f"- الحد الأدنى للربح: {user.min_profit_percentage}%\n"
            f"- الحد الأقصى للخسارة اليومية: {user.max_daily_loss} USDT\n"
            f"- عدد الصفقات المسجلة: {trades_count}\n"
            f"- إجمالي الأرباح المسجلة: {total_profit_val:.2f} USDT\n"
        )
    await call.message.edit_text(txt, reply_markup=get_main_menu_keyboard())

# --- 10) تحليل السوق عبر OpenAI ---
async def get_market_analysis():
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful crypto market analyst."},
                {"role": "user", "content": "اعطني ملخص تحليل سوق العملات الرقمية الحالي مع بعض العملات الرئيسية."}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ خطأ في جلب تحليل السوق: {str(e)}"

@dp.callback_query_handler(lambda c: c.data == "menu_market_status")
async def market_status_handler(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("⏳ جاري تحليل السوق، يرجى الانتظار...")
    analysis_text = await get_market_analysis()
    await call.message.edit_text(analysis_text, reply_markup=get_main_menu_keyboard())

# --- 11) تشغيل البوت ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
