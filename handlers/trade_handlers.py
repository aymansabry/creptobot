from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler

def setup_trade_handlers(application):
    application.add_handler(CallbackQueryHandler(trade_menu_handler, pattern="^trade_"))

async def trade_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "trade_start":
        await start_trading_flow(query, context)
    elif query.data == "trade_portfolio":
        await show_portfolio(query, context)
    elif query.data == "trade_invest":
        await invest_amount(query, context)

async def start_trading_flow(query, context):
    decision_maker = context.bot_data["decision_maker"]
    trade_executor = context.bot_data["trade_executor"]

    # طلب صفقة من الذكاء الاصطناعي
    opportunity = await decision_maker.get_best_opportunity()

    if not opportunity:
        await query.edit_message_text("❌ لا توجد فرصة تداول مناسبة حاليًا.")
        return

    # تنفيذ الصفقة فعليًا
    result = await trade_executor.execute_trade(opportunity)

    if result["success"]:
        await query.edit_message_text(
            f"✅ تم تنفيذ صفقة:\n\n"
            f"الزوج: {opportunity['pair']}\n"
            f"الربح المتوقع: {opportunity['expected_profit']}%"
        )
    else:
        await query.edit_message_text(f"⚠️ فشل تنفيذ الصفقة: {result['error']}")

async def show_portfolio(query, context):
    user_id = query.from_user.id
    db_session_factory = context.bot_data["db_session"]
    async with db_session_factory() as session:
        # جلب المحفظة من قاعدة البيانات
        from db.models import User
        user = await session.get(User, user_id)

        if not user:
            await query.edit_message_text("❌ لم يتم العثور على بيانات محفظتك.")
            return

        await query.edit_message_text(
            f"💼 محفظتك:\n\n"
            f"الرصيد: {user.balance:.2f} USDT\n"
            f"استثمار حالي: {user.investment:.2f} USDT"
        )

async def invest_amount(query, context):
    user_id = query.from_user.id
    db_session_factory = context.bot_data["db_session"]
    async with db_session_factory() as session:
        from db.models import User
        user = await session.get(User, user_id)

        if not user:
            await query.edit_message_text("❌ لم يتم العثور على حسابك.")
            return

        # استثمار وهمي بقيمة 10 USDT
        user.investment += 10
        user.balance -= 10
        await session.commit()

        await query.edit_message_text(
            f"💸 تم استثمار 10 USDT.\n"
            f"الرصيد الجديد: {user.balance:.2f} USDT"
        )