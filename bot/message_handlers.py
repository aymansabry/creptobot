from telegram import Update
from telegram.ext import CallbackContext
from database.init_db import SessionLocal
from database.models import User
from bot.handlers import main_menu

session = SessionLocal()

def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    user = session.query(User).filter_by(telegram_id=str(user_id)).first()
    if not user:
        user = User(telegram_id=str(user_id))
        session.add(user)
        session.commit()

    if context.user_data.get('awaiting_binance'):
        try:
            api_key, api_secret = text.split('|')
            user.binance_api_key = api_key
            user.binance_api_secret = api_secret
            session.commit()
            update.message.reply_text("✅ تم ربط حساب Binance بنجاح!", reply_markup=main_menu())
        except:
            update.message.reply_text("❌ صيغة غير صحيحة. أرسل بالشكل: `API_KEY|API_SECRET`")
        context.user_data['awaiting_binance'] = False

    elif context.user_data.get('awaiting_balance'):
        try:
            user.balance = float(text)
            session.commit()
            update.message.reply_text(f"✅ تم تحديث الرصيد إلى: ${user.balance}", reply_markup=main_menu())
        except:
            update.message.reply_text("❌ صيغة غير صحيحة. أرسل رقم فقط.")
        context.user_data['awaiting_balance'] = False
