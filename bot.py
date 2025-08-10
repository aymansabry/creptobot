import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.filters import StateFilter
from sqlalchemy import and_
from cryptography.fernet import Fernet, InvalidToken
import datetime

from database import create_tables, SessionLocal
from models import User, APIKey, TradeLog
from settings import BOT_TOKEN, OWNER_ID, FERNET_KEY

# إنشاء الجداول قبل بدء البوت
create_tables()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

fernet = Fernet(FERNET_KEY.encode())

class InvestmentStates(StatesGroup):
    waiting_for_investment_amount = State()

# قوائم المستخدمين
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/help"), KeyboardButton(text="تسجيل/تعديل بيانات التداول")],
        [KeyboardButton(text="ابدأ استثمار"), KeyboardButton(text="استثمار وهمي")],
        [KeyboardButton(text="كشف حساب عن فترة"), KeyboardButton(text="حالة السوق")],
        [KeyboardButton(text="ايقاف الاستثمار")]
    ],
    resize_keyboard=True
)

owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/help"), KeyboardButton(text="/admin_panel")],
        [KeyboardButton(text="تعديل نسبة ربح البوت"), KeyboardButton(text="عدد المستخدمين")],
        [KeyboardButton(text="عدد المستخدمين أونلاين"), KeyboardButton(text="تقارير الاستثمار")],
        [KeyboardButton(text="حالة البوت البرمجية")]
    ],
    resize_keyboard=True
)

def safe_decrypt(token):
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == int(OWNER_ID):
        await message.answer("أهلاً مالك البوت!", reply_markup=owner_keyboard)
    else:
        await message.answer("أهلاً! البوت يعمل بنجاح.", reply_markup=user_keyboard)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.reply(
        "هذه أوامر البوت المتاحة:\n"
        "/start\n"
        "/help\n"
        "تسجيل/تعديل بيانات التداول\n"
        "ابدأ استثمار\n"
        "استثمار وهمي\n"
        "كشف حساب عن فترة\n"
        "حالة السوق\n"
        "ايقاف الاستثمار\n"
    )

@dp.message(Text("تسجيل/تعديل بيانات التداول"))
async def handle_api_key_entry(message: types.Message):
    # هنا تبدأ حوارات تسجيل/تعديل مفاتيح API - تحتاج إضافة منطقك هنا
    await message.answer("يرجى اختيار المنصة وإدخال مفاتيح API (قيد التطوير).")

@dp.message(Text("ابدأ استثمار"))
async def start_investment(message: types.Message, state: FSMContext):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("يجب تسجيل بيانات التداول أولاً عبر 'تسجيل/تعديل بيانات التداول'.")
            return
        if not user.is_active:
            await message.answer("تم إيقاف الاستثمار الخاص بك، لا يمكنك البدء حالياً.")
            return
    await message.answer("أدخل مبلغ الاستثمار (مثلاً: 1000):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InvestmentStates.waiting_for_investment_amount)

@dp.message(StateFilter(InvestmentStates.waiting_for_investment_amount))
async def process_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("يرجى إدخال مبلغ صحيح أكبر من صفر.")
        return

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer("لم يتم العثور على بيانات المستخدم.")
            await state.clear()
            return

        # تحديث مبلغ الاستثمار وتفعيل المستخدم
        user.investment_amount = amount
        user.is_active = True
        session.commit()

    await message.answer(f"تم تعيين مبلغ الاستثمار: {amount} بنجاح.\nيتم الآن بدء الاستثمار الآلي...")
    await state.clear()

    # استدعاء دالة تنفيذ الاستثمار (تحتاج بناء هذه الدالة)
    await run_investment_for_user(user)

async def run_investment_for_user(user: User):
    # هذه الدالة مثال مبدئي يجب استكمالها حسب منطق الاستثمار الفعلي
    with SessionLocal() as session:
        api_keys = session.query(APIKey).filter(
            APIKey.user_id == user.id,
            APIKey.is_active == True
        ).all()

    # هنا تقوم بالتعامل مع مفاتيح API وبدء عملية المراجحة أو الاستثمار
    for key in api_keys:
        exchange_name = key.exchange
        # تنفيذ تداولات أو استدعاء API تبعًا للمنصة

    # يمكنك إضافة لوجيك تسجيل التداولات في TradeLog

@dp.message(Text("استثمار وهمي"))
async def fake_investment(message: types.Message):
    await message.answer("ميزة الاستثمار الوهمي قيد التطوير...")

@dp.message(Text("كشف حساب عن فترة"))
async def account_statement(message: types.Message):
    await message.answer("يرجى إد