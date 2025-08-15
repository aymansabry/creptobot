import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import BOT_TOKEN, ADMIN_ID, OPENAI_API_KEY
from db.db_setup import SessionLocal, User
from arbitrage import run_arbitrage, demo_arbitrage
import openai

# ----------------- Logging -----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------- إعداد البوت -----------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
openai.api_key = OPENAI_API_KEY

# ----------------- أحداث أوامر المستخدم -----------------
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply("مرحبًا بالمدير!\nأوامر متاحة:\n"
                            "/edit_profit - تعديل نسبة ربح البوت\n"
                            "/total_users - إجمالي المستخدمين\n"
                            "/online_users - المستخدمين أونلاين\n"
                            "/investment_reports - تقارير الاستثمار\n"
                            "/bot_status - حالة البوت\n"
                            "/trade_as_user - التداول كمستخدم عادي")
    else:
        await message.reply("مرحبًا!\nأوامر متاحة:\n"
                            "/manage_trading - إدارة بيانات التداول\n"
                            "/start_investment - ابدأ الاستثمار\n"
                            "/demo_investment - استثمار وهمي\n"
                            "/account_statement - كشف حساب\n"
                            "/stop_investment - إيقاف الاستثمار\n"
                            "/market_status - حالة السوق")

# ----------------- أوامر المدير -----------------
@dp.message_handler(commands=['edit_profit', 'total_users', 'online_users',
                             'investment_reports', 'bot_status', 'trade_as_user'])
async def admin_commands(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("أمر غير مصرح به.")
        return

    if message.text == "/edit_profit":
        await message.reply("أدخل نسبة ربح البوت الجديدة:")
    elif message.text == "/total_users":
        total = await get_total_users()
        await message.reply(f"إجمالي عدد المستخدمين: {total}")
    elif message.text == "/online_users":
        online = await get_online_users()
        await message.reply(f"عدد المستخدمين أونلاين: {online}")
    elif message.text == "/investment_reports":
        await message.reply("اختر الفترة لتقارير الاستثمار.")
    elif message.text == "/bot_status":
        status = await get_bot_status()
        await message.reply(f"حالة البوت: {status}")
    elif message.text == "/trade_as_user":
        await message.reply("أدخل بيانات المستخدم للتداول كمستخدم عادي:")

# ----------------- أوامر المستخدم -----------------
@dp.message_handler(commands=['manage_trading', 'start_investment', 'demo_investment',
                             'account_statement', 'stop_investment', 'market_status'])
async def user_commands(message: types.Message):
    if message.text == "/manage_trading":
        await message.reply("اختر المنصة لإضافة أو تعديل بيانات التداول.")
    elif message.text == "/start_investment":
        await message.reply("تشغيل الاستثمار الفعلي...")
        asyncio.create_task(run_arbitrage.run_arbitrage_for_all_users())
    elif message.text == "/demo_investment":
        await message.reply("تشغيل الاستثمار الوهمي...")
        asyncio.create_task(demo_arbitrage.run_demo_for_all_users())
    elif message.text == "/account_statement":
        await message.reply("اختر بداية الفترة لعرض كشف الحساب.")
    elif message.text == "/stop_investment":
        await message.reply("تم إيقاف الاستثمار الخاص بك.")
    elif message.text == "/market_status":
        analysis = await market_analysis_summary()
        await message.reply(analysis)

# ----------------- وظائف مساعدة المدير -----------------
async def get_total_users():
    session = SessionLocal()
    total = session.query(User).count()
    session.close()
    return total

async def get_online_users():
    return 5  # مثال: يمكن تعديل حسب آخر تفاعل المستخدم

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