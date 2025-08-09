from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from db.models import User
from db.session import get_session
from core.config import MIN_INVESTMENT_USDT

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username

    session = get_session()
    user = session.query(User).filter_by(telegram_id=str(user_id)).first()
    if not user:
        user = User(telegram_id=str(user_id), username=username)
        session.add(user)
        session.commit()
        session.refresh(user)
    session.close()

    keyboard = [
        [InlineKeyboardButton("بدء الاستثمار", callback_data="start_investment")],
        [InlineKeyboardButton("التداول التجريبي", callback_data="start_demo")],
        [InlineKeyboardButton("حساب الأرباح التجريبية", callback_data="demo_profit")],
        [InlineKeyboardButton("معلومات حسابي", callback_data="account_info")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"مرحباً {username}!\nاختر خياراً من القائمة:",
        reply_markup=reply_markup,
    )

async def handle_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    session = get_session()
    user = session.query(User).filter_by(telegram_id=str(user_id)).first()
    if not user:
        await query.message.reply_text("خطأ: المستخدم غير مسجل.")
        session.close()
        return

    if query.data == "start_investment":
        await query.message.reply_text(f"يرجى إدخال مبلغ الاستثمار (≥ {MIN_INVESTMENT_USDT} USDT):")
        context.user_data['awaiting_investment_amount'] = True

    elif query.data == "start_demo":
        user.trading_mode = "demo"
        user.wallet_balance = 1000.0
        user.profit_earned = 0.0
        session.commit()
        await query.message.reply_text("تم تفعيل التداول التجريبي. رصيدك التجريبي 1000 USDT. يمكنك متابعة الأرباح بدون مخاطرة.")

    elif query.data == "demo_profit":
        profit_increment = user.wallet_balance * 0.005
        user.profit_earned += profit_increment
        session.commit()
        await query.message.reply_text(f"أرباحك التجريبية الحالية: {user.profit_earned:.2f} USDT")

    elif query.data == "account_info":
        await query.message.reply_text(
            f"حسابك:\n"
            f"نوع التداول: {user.trading_mode}\n"
            f"رصيد المحفظة: {user.wallet_balance:.2f} USDT\n"
            f"الأرباح المتراكمة: {user.profit_earned:.2f} USDT\n"
            f"الحساب نشط: {'نعم' if user.active else 'لا'}"
        )
    session.close()

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    session = get_session()
    user = session.query(User).filter_by(telegram_id=str(user_id)).first()
    if not user:
        await update.message.reply_text("خطأ: المستخدم غير مسجل.")
        session.close()
        return

    if context.user_data.get('awaiting_investment_amount'):
        try:
            amount = float(update.message.text)
            if amount < MIN_INVESTMENT_USDT:
                await update.message.reply_text(f"المبلغ يجب أن يكون على الأقل {MIN_INVESTMENT_USDT} USDT.")
                session.close()
                return

            if user.wallet_balance < amount:
                await update.message.reply_text("رصيد المحفظة غير كافٍ للاستثمار بالمبلغ المطلوب.")
                session.close()
                return

            user.investment_amount = amount
            user.wallet_balance -= amount
            user.trading_mode = "real"

            session.commit()
            await update.message.reply_text(
                f"تم تسجيل مبلغ الاستثمار: {amount} USDT.\nرصيد محفظتك الحالي: {user.wallet_balance:.2f} USDT.\nيمكنك الآن بدء التداول الحقيقي."
            )
            context.user_data['awaiting_investment_amount'] = False
        except ValueError:
            await update.message.reply_text("يرجى إدخال رقم صالح للمبلغ.")
    session.close()
