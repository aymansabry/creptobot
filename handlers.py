import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db import get_session, User
from market import analyze_market
from trading import start_trading_for_user

router = Router()

class InvestState(StatesGroup):
    enter_amount = State()
    enter_binance_keys = State()
    enter_kucoin_keys = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    session = get_session()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        session.add(user)
        session.commit()
        await message.answer("👋 أهلاً! تم إنشاء حسابك في النظام.")
    await message.answer("اختر من القائمة:\n- ربط حساب Binance\n- ربط حساب KuCoin\n- بدء الاستثمار\n- حالة السوق")

@router.message(Command("link_binance"))
async def link_binance(message: types.Message, state: FSMContext):
    await state.set_state(InvestState.enter_binance_keys)
    await message.answer("🔑 أرسل API Key و Secret لـ Binance بهذا الشكل:\n`API_KEY|SECRET`")

@router.message(InvestState.enter_binance_keys)
async def save_binance_keys(message: types.Message, state: FSMContext):
    try:
        api_key, api_secret = message.text.strip().split("|")
        session = get_session()
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            user.set_binance_keys(api_key, api_secret)
            session.commit()
            await message.answer("✅ تم حفظ بيانات Binance بنجاح.")
        await state.clear()
    except:
        await message.answer("❌ صيغة غير صحيحة. أعد المحاولة.")

@router.message(Command("link_kucoin"))
async def link_kucoin(message: types.Message, state: FSMContext):
    await state.set_state(InvestState.enter_kucoin_keys)
    await message.answer("🔑 أرسل API Key و Secret و Passphrase لـ KuCoin بهذا الشكل:\n`API_KEY|SECRET|PASSPHRASE`")

@router.message(InvestState.enter_kucoin_keys)
async def save_kucoin_keys(message: types.Message, state: FSMContext):
    try:
        api_key, api_secret, passphrase = message.text.strip().split("|")
        session = get_session()
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            user.set_kucoin_keys(api_key, api_secret, passphrase)
            session.commit()
            await message.answer("✅ تم حفظ بيانات KuCoin بنجاح.")
        await state.clear()
    except:
        await message.answer("❌ صيغة غير صحيحة. أعد المحاولة.")

@router.message(Command("invest"))
async def invest(message: types.Message, state: FSMContext):
    await state.set_state(InvestState.enter_amount)
    await message.answer("💰 أدخل مبلغ الاستثمار (بالدولار)")

@router.message(InvestState.enter_amount)
async def save_investment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        session = get_session()
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            user.balance = amount
            user.profit = 0
            session.commit()
            await message.answer(f"✅ تم بدء الاستثمار بمبلغ {amount}$.\n🚀 جاري تشغيل التداول...")
            asyncio.create_task(start_trading_for_user(user.telegram_id))
        await state.clear()
    except:
        await message.answer("❌ أدخل رقم صحيح.")

@router.message(Command("market"))
async def market_status(message: types.Message):
    status = await analyze_market()
    await message.answer(f"📊 **حالة السوق الحالية:**\n{status}", parse_mode="Markdown")

@router.message(Command("balance"))
async def check_balance(message: types.Message):
    session = get_session()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    if user:
        await message.answer(f"💰 رصيدك: {user.balance}$\n📈 أرباحك: {user.profit}$\nإجمالي: {user.balance + user.profit}$")
