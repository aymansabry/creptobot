import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from db.db_setup import SessionLocal, User, ExchangeCredential
from arbitrage import run_arbitrage, demo_arbitrage

BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # عدل برقم المدير
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)

# ----------------- Logging -----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------- States لتسجيل المنصات -----------------
class PlatformRegistration(StatesGroup):
    waiting_for_name = State()
    waiting_for_api = State()
    waiting_for_secret = State()
    waiting_for_password = State()

# ----------------- أوامر -----------------
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply("مرحبًا بالمدير! استخدم الأوامر: /add_platform لتسجيل منصة، /run_arbitrage لتشغيل المراجحة.")
    else:
        await message.reply("مرحبًا! استخدم /add_platform لتسجيل منصة و /demo_investment لتجربة وهمية.")

# ----------------- تسجيل منصة -----------------
@dp.message_handler(commands=['add_platform'])
async def start_platform_registration(message: types.Message):
    await message.reply("أدخل اسم المنصة:")
    await PlatformRegistration.waiting_for_name.set()

@dp.message_handler(state=PlatformRegistration.waiting_for_name)
async def platform_name_received(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("أدخل API Key للمنصة:")
    await PlatformRegistration.waiting_for_api.set()

@dp.message_handler(state=PlatformRegistration.waiting_for_api)
async def platform_api_received(message: types.Message, state: FSMContext):
    await state.update_data(api_key=message.text)
    await message.reply("أدخل Secret Key للمنصة:")
    await PlatformRegistration.waiting_for_secret.set()

@dp.message_handler(state=PlatformRegistration.waiting_for_secret)
async def platform_secret_received(message: types.Message, state: FSMContext):
    await state.update_data(secret_key=message.text)
    await message.reply("أدخل كلمة المرور الخاصة بالمنصة (اختياري):")
    await PlatformRegistration.waiting_for_password.set()

@dp.message_handler(state=PlatformRegistration.waiting_for_password)
async def platform_password_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    password = message.text if message.text else None

    session = SessionLocal()
    credential = ExchangeCredential(
        user_id=message.from_user.id,
        exchange_name=data['name'],
        api_key=data['api_key'],
        secret_key=data['secret_key'],
        password=password
    )
    session.add(credential)
    session.commit()
    session.close()

    await message.reply(f"تم تسجيل منصة {data['name']} بنجاح!")
    await state.finish()

# ----------------- أوامر إضافية -----------------
@dp.message_handler(commands=['run_arbitrage'])
async def run_real_arbitrage(message: types.Message):
    await message.reply("تشغيل المراجحة الفعلية لجميع المستخدمين...")
    asyncio.create_task(run_arbitrage.run_arbitrage_for_all_users())

@dp.message_handler(commands=['demo_investment'])
async def run_demo_investment(message: types.Message):
    await message.reply("تشغيل المراجحة الوهمية لجميع المستخدمين...")
    asyncio.create_task(demo_arbitrage.run_demo_for_all_users())

# ----------------- تشغيل البوت -----------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)