from telegram import Update
from telegram.ext import CallbackContext
from database.init_db import SessionLocal
from database.models import User
from bot.handlers import main_menu
from bot.settings import settings_menu

session = SessionLocal()

def handle_settings_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    user = session.query(User).filter_by(telegram_id=str(user_id)).first()
    if not user:
        user = User(telegram_id=str(user_id))
        session.add(user)
        session.commit()

    if query.data == 'link_binance':
        context.user_data['awaiting_binance'] = True
        query.edit_message_text("🔑 أرسل مفتاح Binance بهذا الشكل:\n`API_KEY|API_SECRET`")

    elif query.data == 'edit_balance':
        context.user_data['awaiting_balance'] = True
        query.edit_message_text("💰 أرسل الرصيد الجديد بالأرقام فقط.")

    elif query.data == 'back_to_main':
        query.edit_message_text("🏠 رجوع للقائمة الرئيسية", reply_markup=main_menu())
