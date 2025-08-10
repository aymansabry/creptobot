import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text, StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from cryptography.fernet import Fernet, InvalidToken
import datetime
import ccxt.async_support as ccxt_async
import logging
import openai
import os

from database import create_tables, SessionLocal
from models import User, APIKey, TradeLog
from settings import BOT_TOKEN, OWNER_ID, FERNET_KEY, OPENAI_API_KEY

# تهيئة اللوغGING
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تهيئة بوت وديسباتشر
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# تهيئة Fernet للتشفير
fernet = Fernet(FERNET_KEY.encode())

# تهيئة OpenAI
openai.api_key = OPENAI_API_KEY

create_tables()

# حالات FSM
class InvestmentStates(StatesGroup):
    waiting_for_exchange_name = State()
    waiting_for_api_key = State()
    waiting_for_api_secret = State()
    waiting_for_passphrase = State()
    waiting_for_investment_amount = State()
    waiting_for_report_start_date = State()
    waiting_for_profit_percentage = State()
    waiting_for_strategy_choice = State()
    waiting_for_stop_loss = State()
    waiting_for_take_profit = State()


# لوحات أزرار
user_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="مساعدة /help", callback_data="help"),
     InlineKeyboardButton(text="تسجيل/تعديل بيانات التداول", callback_data="register_trading_data")],
    [InlineKeyboardButton(text="ابدأ استثمار", callback_data="start_investment"),
     InlineKeyboardButton(text="استثمار وهمي", callback_data="fake_investment")],
    [InlineKeyboardButton(text="كشف حساب عن فترة", callback_data="account_statement"),
     InlineKeyboardButton(text="حالة السوق", callback_data="market_status")],
    [InlineKeyboardButton(text="ايقاف الاستثمار", callback_data="stop_investment")]
])

owner_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="/help", callback_data="help"),
     InlineKeyboardButton(text="/admin_panel", callback_data="admin_panel")],
    [InlineKeyboardButton(text="تعديل نسبة ربح البوت", callback_data="edit_profit_percentage"),
     InlineKeyboardButton(text="عدد المستخدمين", callback_data="user_count")],
    [InlineKeyboardButton(text="عدد المستخدمين أونلاين", callback_data="online_user_count"),
     InlineKeyboardButton(text="تقارير الاستثمار", callback_data="investment_reports")],
    [InlineKeyboardButton(text="حالة البوت البرمجية", callback_data="bot_status"),
     InlineKeyboardButton(text="تبديل وضع المستخدم/مالك", callback_data="toggle_user_owner")]
])

# دوال تشفير وفك تشفير
def safe_encrypt(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

def safe_decrypt(token: str) -> str | None:
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None

# دالة لفحص صلاحية API Key عبر ccxt
async def verify_api_key(exchange_name: str, api_key: str, api_secret: str, passphrase: str | None = None) -> bool:
    try:
        exchange_class = getattr(ccxt_async, exchange_name)
        kwargs = {
            "apiKey": api_key,
            "secret": api_secret,
        }
        if passphrase:
            kwargs["password"] = passphrase
        
        exchange = exchange_class(kwargs)
        await exchange.load_markets()
        await exchange.close()
        return True
    except Exception as e:
        logger.error(f"API Key verification failed for {exchange_name}: {e}")
        return False

# دالة استراتيجيات التداول (مثال بسيط مع SMA crossover)
async def trading_strategy(exchange, symbol: str, amount: float, stop_loss_pct: float, take_profit_pct: float):
    try:
        # جلب بيانات الشموع (آخر 50 شمعة 1 دقيقة)
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1m', limit=50)
        closes = [candle[4] for candle in ohlcv]

        # حساب متوسطات متحركة بسيطة
        sma_short = sum(closes[-10:]) / 10
        sma_long = sum(closes[-30:]) / 30

        last_price = closes[-1]
        logger.info(f"Last price: {last_price}, SMA10: {sma_short}, SMA30: {sma_long}")

        # حالات الدخول والخروج
        # إذا SMA10 تقاطع فوق SMA30 => شراء
        # إذا SMA10 تقاطع تحت SMA30 => بيع (إغلاق الصفقة)

        positions = await exchange.fetch_positions() if hasattr(exchange, 'fetch_positions') else None

        if sma_short > sma_long:
            # فتح صفقة شراء لو ما فيش صفقة مفتوحة
            logger.info("Signal to BUY")
            order = await exchange.create_market_buy_order(symbol, amount)
            logger.info(f"Buy order placed: {order}")
            # لاحقا يمكن إضافة وقف خسارة وجني أرباح تلقائي
        elif sma_short < sma_long:
            # إغلاق الصفقة لو مفتوحة
            logger.info("Signal to SELL")
            order = await exchange.create_market_sell_order(symbol, amount)
            logger.info(f"Sell order placed: {order}")

    except Exception as e:
        logger.error(f"Error in trading strategy: {e}")

# دالة تشغيل الاستثمار لكل مستخدم بشكل دوري مع مراقبة وإدارة مخاطر
async def run_investment_for_user(user_id: int, amount: float, stop_loss_pct: float = 0.02, take_profit_pct: float = 0.05):
    with SessionLocal() as session:
        api_key_record = session.query(APIKey).filter_by(user_id=user_id).first()
        if not api_key_record:
            logger.warning(f"User {user_id} has no API keys registered.")
            return
        
        exchange_name = api_key_record.exchange.lower()
        api_key = safe_decrypt(api_key_record.api_key)
        api_secret = safe_decrypt(api_key_record.api_secret)
        passphrase = safe_decrypt(api_key_record.passphrase) if api_key_record.passphrase else None

    try:
        exchange_class = getattr(ccxt_async, exchange_name)
        exchange = exchange_class({
            "apiKey": api_key,
            "secret": api_secret,
            "password": passphrase
        })

        symbol = 'BTC/USDT'  # مثال: يمكن إضافة اختيار رمز ديناميكي لاحقاً

        # تحقق من صحة المفتاح
        if not await verify_api_key(exchange_name, api_key, api_secret, passphrase):
            logger.warning(f"API keys for user {user_id} are invalid or expired.")
            await bot.send_message(user_id, "مفاتيح API الخاصة بك غير صحيحة أو منتهية الصلاحية. يرجى تحديثها.")
            await exchange.close()
            return

        # تنفيذ الاستراتيجية
        await trading_strategy(exchange, symbol, amount, stop_loss_pct, take_profit_pct)
        await exchange.close()
    except Exception as e:
        logger.error(f"Error during investment run for user {user_id}: {e}")
        try:
            await bot.send_message(user_id, f"حدث خطأ أثناء تنفيذ التداول: {e}")
        except Exception as inner_e:
            logger.error(f"Failed to send error message to user {user_id}: {inner_e}")

# دوال أوامر بوت (اختصار لأوامر فقط)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            # سجل مستخدم جديد
            user = User(telegram_id=message.from_user.id, is_owner=(message.from_user.id == int(OWNER_ID)))
            session.add(user)
            session.commit()

        if user.is_owner:
            await message.answer("أهلاً مالك البوت!", reply_markup=owner_inline_keyboard)
        else:
            await message.answer("أهلاً! البوت يعمل بنجاح.", reply_markup=user_inline_keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "أوامر البوت:\n"
        "/start - بدء البوت\n"
        "/help - عرض هذه الرسالة\n"
        "تسجيل/تعديل بيانات التداول - لربط حسابك بمنصة تداول\n"
        "ابدأ استثمار - لتفعيل التداول الآلي\n"
        "استثمار وهمي - لتجربة التداول بدون مخاطرة\n"
        "كشف حساب عن فترة - للحصول على تقرير بالأرباح والخسائر\n"
        "حالة السوق - لعرض أحدث بيانات السوق\n"
        "ايقاف الاستثمار - لإيقاف التداول الآلي\n"
    )
    await message.answer(help_text)

# باقي الدوال المرتبطة بالأزرار هنا (تسجيل API, الاستثمار, التقارير, السوق...) مع إضافة دعم OpenAI لتحليل ذكي

# دالة تحليل أخبار أو تحليلات السوق باستخدام OpenAI
async def openai_market_analysis(prompt: str) -> str:
    try:
        response = await openai.Completion.acreate(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7,
            n=1,
            stop=None,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "عذرًا، لم أتمكن من الحصول على تحليل السوق الآن."

@dp.callback_query(Text("market_status"))
async def market_status_report(callback_query: types.CallbackQuery):
    exchange = ccxt_async.binance()
    try:
        tickers = await exchange.fetch_tickers()
        btc_price = tickers['BTC/USDT']['last']
        eth_price = tickers['ETH/USDT']['last']

        # استخدم OpenAI لتحليل سريع
        prompt = f"تحليل مختصر لوضع سوق العملات الرقمية الحالية مع سعر BTC {btc_price} وسعر ETH {eth_price}."
        analysis = await openai_market_analysis(prompt)

        msg = (f"**حالة السوق الحالية:**\n\n"
               f"سعر BTC/USDT: {btc_price:.2f} $\n"
               f"سعر ETH/USDT: {eth_price:.2f} $\n\n"
               f"تحليل: {analysis}")

        await callback_query.message.answer(msg)
    except Exception as e:
        await callback_query.message.answer(f"حدث خطأ أثناء جلب بيانات السوق: {e}")
    finally:
        await exchange.close()
    await callback_query.answer()

# دالة تشغيل البوت
async def main():
    logger.info("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("البوت توقف عن العمل")