from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from database import Database, ExchangePlatform, User, ExchangeConnection
from config import Config
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time
import asyncio

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# تهيئة البوت
bot = Bot(token=Config.USER_BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())
db = Database()

# حالات المستخدم
class UserStates(StatesGroup):
    waiting_exchange = State()
    waiting_api_key = State()
    waiting_api_secret = State()
    waiting_passphrase = State()
    waiting_investment = State()
    waiting_report_date = State()
    waiting_confirmation = State()

async def on_startup(dp):
    logger.info("Bot started successfully")
    await bot.send_message(Config.ADMIN_ID, "✅ البوت يعمل الآن")

async def on_shutdown(dp):
    logger.info("Bot is shutting down...")
    await bot.send_message(Config.ADMIN_ID, "⛔ البوت يتوقف الآن")
    await dp.storage.close()
    await dp.storage.wait_closed()

# ---- وظائف مساعدة ----
async def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📊 بيانات التداول", "💰 إدارة الاستثمار")
    keyboard.row("📈 حالة السوق", "📅 كشف حساب")
    return keyboard

async def show_main_menu(message: types.Message):
    try:
        keyboard = await get_main_keyboard()
        await message.answer("مرحباً بك في بوت التداول الذكي!\nاختر من القائمة:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in show_main_menu: {e}")
        await message.answer("❌ حدث خطأ في عرض القائمة الرئيسية")

# ---- معالجة الأوامر والرسائل ----
@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    try:
        user = db.get_user(message.from_user.id)
        if not user:
            user_data = {
                'telegram_id': message.from_user.id,
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'balance': 0.0,
                'demo_balance': 10000.0
            }
            if db.add_user(user_data):
                await message.answer("🎉 تم تسجيلك بنجاح في النظام!")
            else:
                await message.answer("❌ فشل في تسجيل البيانات، يرجى المحاولة لاحقاً")
                return
        
        await show_main_menu(message)
    except Exception as e:
        logger.error(f"Error in /start command: {e}")
        await message.answer("❌ حدث خطأ أثناء معالجة طلبك، يرجى المحاولة لاحقاً")

@dp.message_handler(text="📊 بيانات التداول")
async def trading_data(message: types.Message):
    try:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("➕ ربط منصة جديدة", callback_data="connect_exchange"),
            types.InlineKeyboardButton("⚙️ إدارة المنصات", callback_data="manage_exchanges"),
            types.InlineKeyboardButton("👛 رصيد المحفظة", callback_data="wallet_balance")
        )
        await message.answer("إدارة بيانات التداول:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in trading_data: {e}")
        await message.answer("❌ حدث خطأ في عرض خيارات التداول")

# ... (بقية الدوال تبقى كما هي مع إضافة معالجة الأخطاء)

@dp.callback_query_handler(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
        await show_main_menu(callback.message)
    except Exception as e:
        logger.error(f"Error in back_to_main: {e}")
        await callback.answer("❌ حدث خطأ أثناء العودة للقائمة الرئيسية")

async def set_commands(bot: Bot):
    commands = [
        types.BotCommand("start", "بدء استخدام البوت"),
        types.BotCommand("help", "مساعدة")
    ]
    await bot.set_my_commands(commands)

if __name__ == '__main__':
    from aiogram import executor
    
    # تنظيف أي عمليات معلقة
    asyncio.get_event_loop().run_until_complete(bot.delete_webhook(drop_pending_updates=True))
    
    try:
        executor.start_polling(
            dp,
            skip_updates=True,
            timeout=30,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            relax=0.1
        )
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")