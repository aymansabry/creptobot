# handlers.py
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils.encryption import encrypt_text, decrypt_text
from db_access import create_or_get_user, save_account_keys, save = None  # placeholder not used
from db_access import save_account_keys as db_save_keys, get_user_by_telegram, get_account_balance, fetch_live_accounts
from db_access import create_or_get_user as db_create_user
from exchange_utils import validate_binance, validate_kucoin
from market import analyze_market, suggest_trades

router = Router()

class UserStates(StatesGroup):
    choosing_exchange = State()
    entering_binance_key = State()
    entering_binance_secret = State()
    entering_kucoin_key = State()
    entering_kucoin_secret = State()
    entering_kucoin_passphrase = State()
    entering_investment = State()

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("بدء استثمار ▶️", callback_data="start_invest")],
        [InlineKeyboardButton("📊 حالة السوق", callback_data="market_status")],
        [InlineKeyboardButton("💡 اقتراحات", callback_data="suggest_trades")],
        [InlineKeyboardButton("💼 محفظتي", callback_data="my_portfolio")],
    ])

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    db_create_user(message.from_user.id)
    await message.answer("أهلاً! اختر من القائمة:", reply_markup=main_kb())

# Menu callbacks
@router.callback_query(F.data == "market_status")
async def cb_market_status(cb: CallbackQuery):
    await cb.message.answer("⏳ جلب وتحليل حالة السوق...")
    summary = await analyze_market()
    await cb.message.answer(summary)
    await cb.answer()

@router.callback_query(F.data == "suggest_trades")
async def cb_suggest(cb: CallbackQuery):
    await cb.message.answer("⏳ أطلب اقتراحات من الذكاء الاصطناعي...")
    s = await suggest_trades()
    await cb.message.answer(s)
    await cb.answer()

@router.callback_query(F.data == "my_portfolio")
async def cb_portfolio(cb: CallbackQuery):
    bal = get_account_balance(cb.from_user.id)
    await cb.message.answer(f"💰 استثمار: {bal['investment']:.2f}$\n📈 أرباح: {bal['pnl']:.6f}$\nرصيد: {bal['balance']:.6f}$")
    await cb.answer()

# Start investment flow
@router.callback_query(F.data == "start_invest")
async def cb_start_invest(cb: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Binance", callback_data="exchange_binance"), InlineKeyboardButton("KuCoin", callback_data="exchange_kucoin")]
    ])
    await cb.message.answer("اختر المنصة لربطها واستثمار مبلغ عليها:", reply_markup=kb)
    await state.set_state(UserStates.choosing_exchange)
    await cb.answer()

@router.callback_query(F.data.startswith("exchange_"))
async def cb_choose_exchange(cb: CallbackQuery, state: FSMContext):
    exch = cb.data.split("_",1)[1]
    await state.update_data(exchange=exch)
    await cb.message.answer(f"أرسل الآن {exch} API Key:")
    if exch == "binance":
        await state.set_state(UserStates.entering_binance_key)
    else:
        await state.set_state(UserStates.entering_kucoin_key)
    await cb.answer()

@router.message(UserStates.entering_binance_key)
async def bin_key(msg: Message, state: FSMContext):
    await state.update_data(binance_key=msg.text.strip())
    await msg.answer("أرسل الآن Binance Secret:")
    await state.set_state(UserStates.entering_binance_secret)

@router.message(UserStates.entering_binance_secret)
async def bin_secret(msg: Message, state: FSMContext):
    data = await state.get_data()
    key = data.get("binance_key")
    secret = msg.text.strip()
    await msg.answer("🔎 جارٍ التحقق من مفاتيح Binance...")
    ok = await validate_binance(key, secret)
    if not ok:
        await msg.answer("❌ فشل التحقق من مفاتيح Binance. تحقق من الصلاحيات (Spot/Trade) ثم أعد المحاولة.")
        return
    # تشفير وحفظ
    enc_key = encrypt_text(key)
    enc_secret = encrypt_text(secret)
    db_save_keys(msg.from_user.id, "binance", api_key=enc_key, api_secret=enc_secret)
    await msg.answer("✅ تم حفظ مفاتيح Binance بنجاح.\nالآن أدخل مبلغ الاستثمار (USD):")
    await state.set_state(UserStates.entering_investment)

@router.message(UserStates.entering_kucoin_key)
async def ku_key(msg: Message, state: FSMContext):
    await state.update_data(kucoin_key=msg.text.strip())
    await msg.answer("أرسل الآن KuCoin Secret:")
    await state.set_state(UserStates.entering_kucoin_secret)

@router.message(UserStates.entering_kucoin_secret)
async def ku_secret(msg: Message, state: FSMContext):
    await state.update_data(kucoin_secret=msg.text.strip())
    await msg.answer("أرسل الآن KuCoin Passphrase:")
    await state.set_state(UserStates.entering_kucoin_passphrase)

@router.message(UserStates.entering_kucoin_passphrase)
async def ku_pass(msg: Message, state: FSMContext):
    data = await state.get_data()
    key = data.get("kucoin_key")
    secret = data.get("kucoin_secret")
    passphrase = msg.text.strip()
    await msg.answer("🔎 جارٍ التحقق من مفاتيح KuCoin...")
    ok = await validate_kucoin(key, secret, passphrase)
    if not ok:
        await msg.answer("❌ فشل التحقق من مفاتيح KuCoin. تأكد من passphrase وحقوق API.")
        return
    enc_key = encrypt_text(key)
    enc_secret = encrypt_text(secret)
    enc_pass = encrypt_text(passphrase)
    db_save_keys(msg.from_user.id, "kucoin", api_key=enc_key, api_secret=enc_secret, passphrase=enc_pass)
    await msg.answer("✅ تم حفظ مفاتيح KuCoin بنجاح.\nالآن أدخل مبلغ الاستثمار (USD):")
    await state.set_state(UserStates.entering_investment)

@router.message(UserStates.entering_investment)
async def enter_invest(msg: Message, state: FSMContext):
    try:
        amount = float(msg.text.strip())
        if amount <= 0:
            raise ValueError()
    except Exception:
        await msg.answer("الرجاء إدخال مبلغ صالح (رقم أكبر من صفر).")
        return
    data = await state.get_data()
    exch = data.get("exchange")
    # حفظ المبلغ وتعيين وضع live
    enc_none = None
    db_save_keys(msg.from_user.id, exch, investment_amount=amount, mode="live")
    await msg.answer(f"✅ تم تفعيل الاستثمار بمبلغ {amount}$ على منصة {exch}. ستبدأ المراجحة التلقائية (إن وُجدت فرص).")
    # تفاعل إحساسي للمستخدم
    await msg.answer("🤖 الذكاء الاصطناعي بدأ العمل لحسابك — ستتلقى تحديثات بعد كل تنفيذ.")
    await state.clear()
