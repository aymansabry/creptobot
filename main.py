import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import BOT_TOKEN, ADMIN_ID, OPENAI_API_KEY
from menus.user_menu import user_main_menu_keyboard
from menus.admin_menu import admin_main_menu_keyboard
from menus.exchange_menu import exchange_selection_keyboard
from arbitrage import run_arbitrage, demo_arbitrage
import openai

# ----------------- Logging -----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------- إعداد البوت -----------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
openai.api_key = OPENAI_API_KEY

# ----------------- أحداث /start -----------------
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("مرحبًا بالمدير! اختر عملية:", reply_markup=admin_main_menu_keyboard())
    else:
        await message.answer("مرحبًا! اختر عملية:", reply_markup=user_main_menu_keyboard())

# ----------------- callback query -----------------
@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    await call.answer()  # مهم جدًا في aiogram 2.x
    logger.info(f"Pressed button: {call.data}")  # للتحقق من الضغط

    # ---------- قوائم المستخدم ----------
    if call.data == "user_manage":
        await call.message.answer(
            "اختر المنصة لإدارة بيانات التداول:", 
            reply_markup=exchange_selection_keyboard()
        )
    elif call.data == "user_start":
        await call.message.answer("تشغيل الاستثمار الفعلي...")
        asyncio.create_task(run_arbitrage.run_arbitrage_for_all_users())
    elif call.data == "user_demo":
        await call.message.answer("تشغيل الاستثمار الوهمي...")
        asyncio.create_task(demo_arbitrage.run_demo_for_all_users())
    elif call.data == "user_statement":
        await call.message.answer("اختر بداية الفترة لعرض كشف الحساب.")
    elif call.data == "user_stop":
        await call.message.answer("تم إيقاف الاستثمار الخاص بك.")
    elif call.data == "market_status":
        analysis = await market_analysis_summary()
        await call.message.answer(analysis)

    # ---------- قوائم المدير ----------
    elif call.data.startswith("admin_"):
        await handle_admin_callbacks(call)

# ----------------- معالجة callbacks المدير -----------------
async def handle_admin_callbacks(call):
    if call.data == "admin_profit":
        await call.message.answer("أدخل نسبة ربح البوت الجديدة:")
    elif call.data == "admin_users":
        total = await get_total_users()
        await call.message.answer(f"إجمالي عدد المستخدمين: {total}")
    elif call.data == "admin_online":
        online = await get_online_users()
        await call.message.answer(f"عدد المستخدمين أونلاين: {online}")
    elif call.data == "admin_reports":
        await call.message.answer("اختر الفترة لتقارير الاستثمار.")
    elif call.data == "admin_status":
        status = await get_bot_status()
        await call.message.answer(f"حالة البوت: {status}")
    elif call.data == "admin_trade_as_user":
        await call.message.answer("أدخل بيانات المستخدم للتداول كمستخدم عادي:")

# ----------------- وظائف مساعدة المدير -----------------
async def get_total_users():
    # مثال ثابت، يمكن ربطه بقاعدة البيانات لاحقًا
    return 100

async def get_online_users():
    # مثال: يمكن حساب المستخدمين النشطين حسب آخر تفاعل
    return 5

async def get_bot_status():
    return "البوت يعمل بشكل طبيعي."

# ----------------- حالة السوق وتحليل OpenAI -----------------
async def market_analysis_summary():
    try:
        prompt = "اعرض ملخص سريع لحالة سوق العملات الرقمية مع نصائح استثمارية قصيرة."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        logger.error(f"OpenAI analysis error: {e}")
        return "لا يمكن الحصول على تحليل السوق حالياً."

# ----------------- تشغيل البوت -----------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)