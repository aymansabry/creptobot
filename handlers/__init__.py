from telegram.ext import Application
from .start import start_handler
from .balance import balance_handler
from .portfolio import portfolio_handler
from .trade import trade_handler
from .admin import admin_handler

def setup_handlers(app: Application):
    app.add_handler(start_handler)
    app.add_handler(balance_handler)
    app.add_handler(portfolio_handler)
    app.add_handler(trade_handler)
    app.add_handler(admin_handler)
    print("✅ تم إعداد الـ Handlers")