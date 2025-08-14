import asyncio
import ccxt
from db.models import SessionLocal, ExchangeCredential, ArbitrageHistory, User
from utils.helpers import execute_order_on_exchange, analyze_with_openai

async def run_arbitrage_for_user(user):
    session = SessionLocal()
    exchanges = session.query(ExchangeCredential).filter_by(user_id=user.id, active=True).all()
    if len(exchanges) < 2:
        session.close()
        return

    symbols_set = set()
    for ex in exchanges:
        exchange_class = getattr(ccxt, ex.exchange_id.lower(), None)
        if exchange_class