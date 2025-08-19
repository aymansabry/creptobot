from telegram import Update
from telegram.ext import CallbackContext
from utils.binance_api import BinanceAPI
from utils.strategy import hedge_strategy, calculate_profit
from database.init_db import SessionLocal
from database.models import User, ArbitrageLog

session = SessionLocal()

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if query.data == 'show_prices':
        api = BinanceAPI(test_mode=True)
        btc_price = api.get_price("BTCUSDT")
        eth_price = api.get_price("ETHUSDT")
        query.edit_message_text(f"💰 BTC: ${btc_price}\n💰 ETH: ${eth_price}")

    elif query.data == 'test_trade':
        user = session.query(User).filter_by(telegram_id=str(user_id)).first()
        if not user:
            user = User(telegram_id=str(user_id))
            session.add(user)
            session.commit()

        strategy = hedge_strategy(user.balance)
        api = BinanceAPI(test_mode=True)
        buy_price = api.get_price("BTCUSDT")
        sell_price = buy_price * 1.02  # ربح وهمي 2%
        profit = calculate_profit(buy_price, sell_price, strategy['risky'])

        log = ArbitrageLog(
            user_id=user.id,
            symbol="BTCUSDT",
            amount=strategy['risky'],
            buy_price=buy_price,
            sell_price=sell_price,
            profit=profit
        )
        session.add(log)
        session.commit()

        query.edit_message_text(f"🧪 تجربة تداول وهمي تمت بنجاح!\nربحك: ${profit}")

    elif query.data == 'real_trade':
        query.edit_message_text("🚧 التنفيذ الحقيقي غير مفعل حالياً. سيتم إضافته لاحقًا مع ربط Binance الحقيقي.")

    elif query.data == 'settings':
        query.edit_message_text("⚙️ إعدادات الحساب قيد التطوير. قريبًا ستتمكن من تعديل بياناتك وربط Binance.")
