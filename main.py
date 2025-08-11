import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from database import Database, ExchangePlatform, User, ExchangeConnection
from config import Config
from datetime import datetime, timedelta
from typing import Dict, Any, List
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
    """دالة تنفيذية عند بدء تشغيل البوت"""
    logger.info("Bot started successfully")
    if hasattr(Config, 'ADMIN_ID') and Config.ADMIN_ID:
        try:
            await bot.send_message(
                Config.ADMIN_ID,
                "✅ البوت يعمل الآن\n"
                f"وقت البدء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")

async def on_shutdown(dp):
    """دالة تنفيذية عند إيقاف البوت"""
    logger.info("Bot is shutting down...")
    if hasattr(Config, 'ADMIN_ID') and Config.ADMIN_ID:
        try:
            await bot.send_message(Config.ADMIN_ID, "⛔ البوت يتوقف الآن")
        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {e}")
    
    await dp.storage.close()
    await dp.storage.wait_closed()
    logger.info("Bot shutdown completed")

async def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    """إنشاء لوحة المفاتيح الرئيسية"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📊 بيانات التداول", "💰 إدارة الاستثمار")
    keyboard.row("📈 حالة السوق", "📅 كشف حساب")
    return keyboard

async def show_main_menu(message: types.Message):
    """عرض القائمة الرئيسية"""
    try:
        keyboard = await get_main_keyboard()
        await message.answer("مرحباً بك في بوت التداول الذكي!\nاختر من القائمة:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in show_main_menu: {e}")
        await message.answer("❌ حدث خطأ في عرض القائمة الرئيسية")

@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    """معالجة أمر /start"""
    try:
        user = db.get_user(message.from_user.id)
        if not user:
            user_data = {
                'telegram_id': message.from_user.id,
                'username': message.from_user.username,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name or '',
                'mode': 'demo',
                'investment_amount': 0.0,
                'balance': 0.0,
                'demo_balance': 10000.0,
                'is_active': True
            }
            user = db.add_user(user_data)
            if user:
                await message.answer("🎉 تم تسجيلك بنجاح في النظام!")
            else:
                await message.answer("⚠️ حدث خطأ أثناء التسجيل، يرجى المحاولة لاحقاً")
                return
        
        await show_main_menu(message)
    except Exception as e:
        logger.error(f"Error in /start command: {e}")
        await message.answer("❌ حدث خطأ أثناء معالجة طلبك، يرجى المحاولة لاحقاً")

@dp.message_handler(text="📊 بيانات التداول")
async def trading_data(message: types.Message):
    """عرض خيارات بيانات التداول"""
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

@dp.callback_query_handler(lambda c: c.data == "connect_exchange")
async def connect_exchange(callback: types.CallbackQuery):
    """بدء عملية ربط منصة تداول جديدة"""
    try:
        keyboard = types.InlineKeyboardMarkup()
        for platform in ExchangePlatform:
            keyboard.add(types.InlineKeyboardButton(
                text=platform.value.upper(),
                callback_data=f"select_{platform.value}"
            ))
        await callback.message.edit_text("اختر المنصة لربطها:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in connect_exchange: {e}")
        await callback.answer("❌ حدث خطأ في عرض خيارات المنصات")

@dp.callback_query_handler(lambda c: c.data.startswith("select_"))
async def select_exchange(callback: types.CallbackQuery, state: FSMContext):
    """اختيار منصة التداول"""
    try:
        platform = callback.data.split("_")[1]
        async with state.proxy() as data:
            data['platform'] = platform
        await UserStates.waiting_api_key.set()
        await callback.message.edit_text(f"أدخل مفتاح API لـ {platform.upper()}:")
    except Exception as e:
        logger.error(f"Error in select_exchange: {e}")
        await callback.answer("❌ حدث خطأ في اختيار المنصة")

@dp.message_handler(state=UserStates.waiting_api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    """معالجة مفتاح API"""
    try:
        async with state.proxy() as data:
            data['api_key'] = message.text
        await UserStates.next()
        await message.answer("أدخل السر السري (API Secret):")
    except Exception as e:
        logger.error(f"Error in process_api_key: {e}")
        await message.answer("❌ حدث خطأ في معالجة المفتاح")
        await state.finish()

async def set_bot_commands():
    """تعيين أوامر البوت"""
    commands = [
        types.BotCommand("start", "بدء استخدام البوت"),
        types.BotCommand("help", "مساعدة")
    ]
    await bot.set_my_commands(commands)

if __name__ == '__main__':
    from aiogram import executor
    
    # تنظيف أي عمليات معلقة
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.delete_webhook(drop_pending_updates=True))
    loop.run_until_complete(set_bot_commands())
    
    try:
        executor.start_polling(
            dp,
            skip_updates=True,
            timeout=30,
            relax=0.5,
            on_startup=on_startup,
            on_shutdown=on_shutdown
        )
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")