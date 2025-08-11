from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import Config
from services.database import Database
import logging
import asyncio

# إعدادات البوت
logging.basicConfig(level=logging.INFO)
bot = Bot(token=Config.USER_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = Database()

# حالات المستخدم
class UserStates(StatesGroup):
    waiting_api_key = State()
    waiting_api_secret = State()
    waiting_passphrase = State()
    waiting_investment = State()

# ---- القوائم الرئيسية ----
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🔄 ربط منصات التداول", callback_data="connect_exchange"),
        types.InlineKeyboardButton("💰 إدارة الاستثمار", callback_data="manage_investment"),
        types.InlineKeyboardButton("📊 لوحة التحكم", callback_data="dashboard"),
        types.InlineKeyboardButton("ℹ️ المساعدة", callback_data="help")
    )
    await message.answer("مرحباً بك في بوت التداول الذكي!", reply_markup=keyboard)

# ---- ربط المنصات ----
@dp.callback_query_handler(lambda c: c.data == 'connect_exchange')
async def connect_exchange(callback: types.CallbackQuery):
    keyboard = await db.get_platforms_keyboard()
    await callback.message.edit_text("اختر المنصة لربطها:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('connect_'))
async def process_platform_selection(callback: types.CallbackQuery, state: FSMContext):
    platform = callback.data.split('_')[1]
    async with state.proxy() as data:
        data['platform'] = platform
    
    await UserStates.waiting_api_key.set()
    await callback.message.edit_text(f"أدخل مفتاح API الخاص بمنصة {platform.upper()}:")

@dp.message_handler(state=UserStates.waiting_api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_key'] = message.text
    
    await UserStates.next()
    await message.answer("الآن أدخل السر السري (API Secret):")

@dp.message_handler(state=UserStates.waiting_api_secret)
async def process_api_secret(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_secret'] = message.text
        platform = data['platform']
    
    if platform == 'kucoin':
        await UserStates.next()
        await message.answer("أدخل كلمة المرور (Passphrase) الخاصة بـ KuCoin:")
    else:
        await save_connection(message, state)

async def save_connection(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.from_user.id
        platform = data['platform']
        api_key = data['api_key']
        api_secret = data['api_secret']
        passphrase = data.get('passphrase')
        
        # التحقق من صحة البيانات
        is_valid = await db.validate_api_credentials(platform, api_key, api_secret, passphrase)
        
        if is_valid:
            saved = await db.save_connection(user_id, platform, api_key, api_secret, passphrase)
            if saved:
                await message.answer(f"✅ تم ربط {platform.upper()} بنجاح!")
            else:
                await message.answer("❌ حدث خطأ أثناء حفظ البيانات")
        else:
            await message.answer("❌ مفاتيح API غير صالحة، يرجى المحاولة مرة أخرى")
    
    await state.finish()

# ---- إدارة الاستثمار ----
@dp.callback_query_handler(lambda c: c.data == 'manage_investment')
async def manage_investment(callback: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("💵 تعيين المبلغ", callback_data="set_amount"),
        types.InlineKeyboardButton("🚀 بدء التداول", callback_data="start_trading"),
        types.InlineKeyboardButton("🛑 إيقاف التداول", callback_data="stop_trading"),
        types.InlineKeyboardButton("🔙 الرجوع", callback_data="back_to_main")
    )
    await callback.message.edit_text("إدارة الاستثمار:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'set_amount')
async def set_amount(callback: types.CallbackQuery):
    await UserStates.waiting_investment.set()
    await callback.message.edit_text("أدخل مبلغ الاستثمار (بالـ USDT):")

@dp.message_handler(state=UserStates.waiting_investment)
async def process_investment(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount > 0:
            # هنا سيتم حفظ المبلغ في قاعدة البيانات
            await message.answer(f"✅ تم تعيين مبلغ الاستثمار إلى {amount} USDT")
        else:
            await message.answer("❌ المبلغ يجب أن يكون أكبر من الصفر")
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح")
    
    await state.finish()

# ---- لوحة التحكم ----
@dp.callback_query_handler(lambda c: c.data == 'dashboard')
async def show_dashboard(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    connections = await db.get_user_connections(user_id)
    
    text = "📊 لوحة التحكم\n\n"
    text += f"🔹 عدد المنصات المرتبطة: {len(connections)}\n"
    text += f"🔹 الحالة: {'🟢 نشط' if True else '🔴 متوقف'}\n"  # هنا يجب جلب الحالة الفعلية
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="dashboard"))
    keyboard.add(types.InlineKeyboardButton("🔙 الرجوع", callback_data="back_to_main"))
    
    await callback.message.edit_text(text, reply_markup=keyboard)

# ---- المساعدة ----
@dp.callback_query_handler(lambda c: c.data == 'help')
async def show_help(callback: types.CallbackQuery):
    help_text = """
ℹ️ دليل استخدام البوت:

1. ربط المنصات:
- اختر المنصة وأدخل مفاتيح API

2. إدارة الاستثمار:
- حدد مبلغ الاستثمار
- ابدأ أو أوقف التداول

3. لوحة التحكم:
- عرض إحصائيات وأداء التداول

للأسئلة: @YourSupportBot
"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 الرجوع", callback_data="back_to_main"))
    await callback.message.edit_text(help_text, reply_markup=keyboard)

# ---- الرجوع للقائمة الرئيسية ----
@dp.callback_query_handler(lambda c: c.data == 'back_to_main')
async def back_to_main(callback: types.CallbackQuery):
    await start(callback.message)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
