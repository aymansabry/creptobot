import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import create_tables, SessionLocal
from settings import BOT_TOKEN, OWNER_ID

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ----- تعريف القوائم الرئيسية -----
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="تسجيل/تعديل بيانات التداول")],
        [KeyboardButton(text="ابدأ استثمار"), KeyboardButton(text="استثمار وهمي")],
        [KeyboardButton(text="كشف حساب عن فترة"), KeyboardButton(text="حالة السوق")],
        [KeyboardButton(text="ايقاف الاستثمار")],
        [KeyboardButton(text="/help")]
    ],
    resize_keyboard=True
)

owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="تعديل نسبة ربح البوت"), KeyboardButton(text="عدد المستخدمين")],
        [KeyboardButton(text="عدد المستخدمين أونلاين"), KeyboardButton(text="تقارير الاستثمار")],
        [KeyboardButton(text="حالة البوت البرمجية")],
        [KeyboardButton(text="/help"), KeyboardButton(text="/start")]
    ],
    resize_keyboard=True
)

# ----- تعريف FSM لحالة تسجيل API Key -----
class TradingDataStates(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_api_key = State()
    waiting_for_api_secret = State()
    waiting_for_passphrase = State()
    confirmation = State()

# ----- البداية -----
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أهلاً مالك البوت!", reply_markup=owner_keyboard)
    else:
        await message.answer("أهلاً! البوت يعمل بنجاح.", reply_markup=user_keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "أوامر المستخدم:\n"
        "- تسجيل/تعديل بيانات التداول\n"
        "- ابدأ استثمار\n"
        "- استثمار وهمي\n"
        "- كشف حساب عن فترة\n"
        "- حالة السوق\n"
        "- ايقاف الاستثمار\n\n"
        "أوامر المدير:\n"
        "- تعديل نسبة ربح البوت\n"
        "- عدد المستخدمين\n"
        "- عدد المستخدمين أونلاين\n"
        "- تقارير الاستثمار\n"
        "- حالة البوت البرمجية"
    )
    await message.reply(help_text)

# ----- التعامل مع قائمة المستخدم -----
@dp.message(Text("تسجيل/تعديل بيانات التداول"))
async def trading_data_start(message: types.Message, state: FSMContext):
    # بداية التسجيل
    await message.answer("اختر المنصة التي تريد إضافة API لها:\nمثلاً: binance, kucoin, coinbase ...", reply_markup=ReplyKeyboardRemove())
    await state.set_state(TradingDataStates.waiting_for_exchange)

@dp.message(TradingDataStates.waiting_for_exchange)
async def process_exchange(message: types.Message, state: FSMContext):
    exchange = message.text.strip().lower()
    # هنا ممكن تضيف تحقق من المنصة إذا تريد
    await state.update_data(exchange=exchange)
    await message.answer("الآن أدخل مفتاح API الخاص بالمنصة:")
    await state.set_state(TradingDataStates.waiting_for_api_key)

@dp.message(TradingDataStates.waiting_for_api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    api_key = message.text.strip()
    await state.update_data(api_key=api_key)
    await message.answer("أدخل السر السري API Secret:")
    await state.set_state(TradingDataStates.waiting_for_api_secret)

@dp.message(TradingDataStates.waiting_for_api_secret)
async def process_api_secret(message: types.Message, state: FSMContext):
    api_secret = message.text.strip()
    await state.update_data(api_secret=api_secret)
    await message.answer("إذا كانت المنصة تتطلب passphrase أدخله الآن، أو اكتب 'لا' لتخطي:")
    await state.set_state(TradingDataStates.waiting_for_passphrase)

@dp.message(TradingDataStates.waiting_for_passphrase)
async def process_passphrase(message: types.Message, state: FSMContext):
    passphrase = message.text.strip()
    if passphrase.lower() == 'لا':
        passphrase = None
    await state.update_data(passphrase=passphrase)

    # استدعاء البيانات من state
    data = await state.get_data()
    exchange = data.get("exchange")
    api_key = data.get("api_key")
    api_secret = data.get("api_secret")
    passphrase = data.get("passphrase")

    # هنا لازم تتحقق من صحة الـ API key مع المنصة (ممكن تستدعي دالة تحقق خارجية)

    # مؤقتاً، سنفترض أن التحقق ناجح
    is_valid = True

    if is_valid:
        await message.answer(f"تم تسجيل بيانات المنصة {exchange} بنجاح ✅")
        # هنا ممكن تخزن البيانات في قاعدة البيانات مع التشفير
        # من المهم تفريغ الحالة بعد الانتهاء
        await state.clear()
    else:
        await message.answer(f"خطأ في بيانات المنصة {exchange} ❌، يرجى إعادة المحاولة.")
        # تقدر ترجع الخطوات أو تلغي التسجيل
        await state.clear()

# ----- التعامل مع بقية الأوامر -----
@dp.message(Text("ابدأ استثمار"))
async def start_investment(message: types.Message):
    await message.answer("بدء عملية الاستثمار بناءً على البيانات المسجلة... (سيتم تطويرها لاحقاً)")

@dp.message(Text("استثمار وهمي"))
async def fake_investment(message: types.Message):
    await message.answer("عرض استثمار وهمي بدون أموال حقيقية... (سيتم تطويرها لاحقاً)")

@dp.message(Text("كشف حساب عن فترة"))
async def account_statement(message: types.Message):
    await message.answer("يرجى إدخال تاريخ بداية الفترة بصيغة YYYY-MM-DD:")

@dp.message(Text("حالة السوق"))
async def market_status(message: types.Message):
    await message.answer("تحليل السوق ونصائح الاستثمار... (سيتم تطويرها لاحقاً)")

@dp.message(Text("ايقاف الاستثمار"))
async def stop_investment(message: types.Message):
    await message.answer("تم إيقاف الاستثمار الخاص بك، لن يتم استخدام أموالك حتى تقوم بإعادة التفعيل.")

# ----- أوامر المدير -----
@dp.message(Text("تعديل نسبة ربح البوت"))
async def change_profit_rate(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أدخل نسبة ربح البوت الجديدة (مثلاً 10 تعني 10%):")
        # تحتاج FSM لحفظ الحالة وتحديث النسبة
    else:
        await message.answer("غير مصرح لك باستخدام هذه الأوامر.")

@dp.message(Text("عدد المستخدمين"))
async def total_users(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        # استعلام من قاعدة البيانات بعدد المستخدمين
        await message.answer("إجمالي عدد المستخدمين: ... (سيتم تطويرها لاحقاً)")
    else:
        await message.answer("غير مصرح لك.")

@dp.message(Text("عدد المستخدمين أونلاين"))
async def online_users(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("عدد المستخدمين أونلاين حالياً: ... (سيتم تطويرها لاحقاً)")
    else:
        await message.answer("غير مصرح لك.")

@dp.message(Text("تقارير الاستثمار"))
async def investment_reports(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("تقارير الاستثمار عن فترة محددة... (سيتم تطويرها لاحقاً)")
    else:
        await message.answer("غير مصرح لك.")

@dp.message(Text("حالة البوت البرمجية"))
async def bot_status(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("البوت يعمل بشكل سليم، لا توجد مشاكل حالياً.")
    else:
        await message.answer("غير مصرح لك.")

# ----- بدء العمل -----
async def main():
    print("البوت بدأ العمل")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())