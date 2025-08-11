import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from database import SessionLocal
from models import User
from trading import encrypt_value, decrypt_value, analyze_market, start_trading

router = Router()

# مفتاح التشفير (يُفضل وضعه في env)
FERNET_KEY = Fernet.generate_key()
fernet = Fernet(FERNET_KEY)

# ربط منصة Binance
@router.message(Command("link_binance"))
async def link_binance(message: Message):
    await message.answer("🔑 أرسل لي API Key لـ Binance:")
    await router.data.update({"awaiting_binance_key": True})

@router.message(F.text & (lambda msg, ctx=router.data: ctx.get("awaiting_binance_key")))
async def binance_key_received(message: Message):
    router.data["binance_key"] = message.text
    router.data["awaiting_binance_key"] = False
    await message.answer("🔐 أرسل لي Secret Key لـ Binance:")
    router.data["awaiting_binance_secret"] = True

@router.message(F.text & (lambda msg, ctx=router.data: ctx.get("awaiting_binance_secret")))
async def binance_secret_received(message: Message):
    binance_key = router.data.pop("binance_key")
    binance_secret = message.text
    router.data["awaiting_binance_secret"] = False

    db: Session = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        db.add(user)

    user.binance_api_key = encrypt_value(binance_key)
    user.binance_api_secret = encrypt_value(binance_secret)
    db.commit()
    db.close()

    await message.answer("✅ تم ربط حساب Binance بنجاح.")

# ربط منصة KuCoin
@router.message(Command("link_kucoin"))
async def link_kucoin(message: Message):
    await message.answer("🔑 أرسل لي API Key لـ KuCoin:")
    router.data["awaiting_kucoin_key"] = True

@router.message(F.text & (lambda msg, ctx=router.data: ctx.get("awaiting_kucoin_key")))
async def kucoin_key_received(message: Message):
    router.data["kucoin_key"] = message.text
    router.data["awaiting_kucoin_key"] = False
    await message.answer("🔐 أرسل لي Secret Key لـ KuCoin:")
    router.data["awaiting_kucoin_secret"] = True

@router.message(F.text & (lambda msg, ctx=router.data: ctx.get("awaiting_kucoin_secret")))
async def kucoin_secret_received(message: Message):
    kucoin_key = router.data.pop("kucoin_key")
    kucoin_secret = message.text
    router.data["awaiting_kucoin_secret"] = False

    db: Session = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id)
        db.add(user)

    user.kucoin_api_key = encrypt_value(kucoin_key)
    user.kucoin_api_secret = encrypt_value(kucoin_secret)
    db.commit()
    db.close()

    await message.answer("✅ تم ربط حساب KuCoin بنجاح.")

# عرض حالة السوق
@router.message(Command("market_status"))
async def market_status(message: Message):
    analysis = analyze_market()
    await message.answer(f"📊 **تحليل السوق الحالي:**\n\n{analysis}", parse_mode="Markdown")

# عرض الرصيد والأرباح
@router.message(Command("portfolio"))
async def portfolio(message: Message):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    db.close()

    if not user:
        await message.answer("⚠️ لم تبدأ الاستثمار بعد.")
        return

    await message.answer(
        f"💰 رصيدك الحالي: {user.balance:.2f}$\n"
        f"📈 أرباحك الإجمالية: {user.profits:.2f}$"
    )

# بدء الاستثمار
@router.message(Command("start_trading"))
async def start_trading_cmd(message: Message):
    await message.answer("💵 أدخل المبلغ الذي تريد استثماره:")
    router.data["awaiting_invest_amount"] = True

@router.message(F.text & (lambda msg, ctx=router.data: ctx.get("awaiting_invest_amount")))
async def invest_amount_received(message: Message):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("❌ أدخل رقم صحيح.")
        return

    router.data["awaiting_invest_amount"] = False

    db: Session = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not user:
        user = User(telegram_id=message.from_user.id, balance=amount)
        db.add(user)
    else:
        user.balance += amount
    db.commit()
    db.close()

    await message.answer(f"✅ تم إضافة {amount}$ لرصيدك.\n🤖 جاري بدء التداول ...")
    await start_trading(message.from_user.id)
