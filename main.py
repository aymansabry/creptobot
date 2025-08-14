import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import BOT_TOKEN, ADMIN_ID, OPENAI_API_KEY
from menus.user_menu import user_main_menu_keyboard
from menus.admin_menu import admin_main_menu_keyboard
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

# ----------------- الأحداث -----------------
@dp.message_handler(commands=['start'])
def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        message.answer("مرحبًا بالمدير! اختر عملية:", reply_markup=admin_main_menu_keyboard())
    else:
        message.answer("مرحبًا! اختر عملية:", reply_markup=user_main_menu_keyboard())

@dp.callback_query_handler(lambda call: True)
def callbacks(call: types.CallbackQuery):
    call.answer()  # مهم جدًا للـ aiogram 2
    # ---------- قوائم المستخدم ----------
    if call.data == "user_manage_trading":
        call.message.answer("اختر المنصة لإضافة أو تعديل بيانات التداول.")
    elif call.data == "user_start_investment":
        call.message.answer("تشغيل الاستثمار الفعلي...")
        asyncio.create_task(run_arbitrage.run_arbitrage_for_all_users())
    elif call.data == "user_demo_investment":
        call.message.answer("تشغيل الاستثمار الوهمي...")
        asyncio.create_task(demo_arbitrage.run_demo_for_all_users())
    elif call.data == "user_account_statement":
        call.message.answer("اختر بداية الفترة لعرض كشف الحساب.")
    elif call.data == "user_stop_investment":
        call.message.answer("تم إيقاف الاستثمار الخاص بك.")
    elif call.data == "market_status":
        analysis = asyncio.run(market_analysis_summary())
        call.message.answer(analysis)

    # ---------- قوائم المدير ----------
    elif call.data.startswith("admin_"):
        handle_admin_callbacks(call)

def handle_admin_callbacks(call):
    if call.data == "admin_edit_bot_profit":
        call.message.answer("أدخل نسبة ربح البوت الجديدة:")
    elif call.data == "admin_total_users":
        total = asyncio.run(get_total_users())
        call.message.answer(f"إجمالي عدد المستخدمين: {total}")
    elif call.data == "admin_online_users":
        online = asyncio.run(get_online_users())
        call.message.answer(f"عدد المستخدمين أونلاين: {online}")
    elif call.data == "admin_investment_reports":
        call.message.answer("اختر الفترة لتقارير الاستثمار.")
    elif call.data == "admin_bot_status":
        status = asyncio.run(get_bot_status())
        call.message.answer(f"حالة البوت: {status}")
    elif call.data == "admin_trade_as_user":
        call.message.answer("أدخل بيانات المستخدم للتداول كمستخدم عادي:")

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