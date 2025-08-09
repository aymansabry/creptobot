# project_root/trading/arbitrage.py (Corrected)
import asyncio
from decimal import Decimal
from core.config import POLL_INTERVAL, MIN_TRADE_USDT, MIN_PROFIT_PCT
from core.logger import get_logger
from db.database import get_session_sync
from db import models
from trading.utils import calc_profit
from exchanges import build_exchange  # This line is now correct
from core.security import decrypt_text
from sqlalchemy.orm import Session
from sqlalchemy import select, update

logger = get_logger('arbitrage')

async def start_arbitrage_loop(testnet=False):
    logger.info('Starting arbitrage loop')
    while True:
        session = get_session_sync()
        try:
            users = session.query(models.User).filter(models.User.enabled == True).all()
            
            tasks = [find_and_execute_trades(session, user, testnet) for user in users]
            await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f'Arbitrage loop error: {e}')
        finally:
            session.close()
        await asyncio.sleep(POLL_INTERVAL)

async def find_and_execute_trades(session: Session, user: models.User, testnet: bool):
    api_block = user.api_exchange or {}
    ex_instances = {}
    
    tasks = []
    for ex_name, cfg in api_block.items():
        if cfg.get('enabled'):
            try:
                cred = {
                    'apiKey': decrypt_text(cfg.get('apiKey')),
                    'secret': decrypt_text(cfg.get('secret')),
                    'password': decrypt_text(cfg.get('password'))
                }
                tasks.append(build_exchange(ex_name, cred))
            except Exception as e:
                logger.error(f'Failed to build exchange {ex_name} for user {user.telegram_id}: {e}')
    
    ex_wrappers = await asyncio.gather(*tasks, return_exceptions=True)
    ex_instances = {wrapper.name: wrapper for wrapper in ex_wrappers if not isinstance(wrapper, Exception)}
    
    if len(ex_instances) < 2:
        for wrapper in ex_instances.values():
            await wrapper.close()
        return

    watch_pairs = ['BTC/USDT', 'ETH/USDT']
    
    for pair in watch_pairs:
        ticker_tasks = {name: inst.fetch_ticker(pair) for name, inst in ex_instances.items()}
        tickers = await asyncio.gather(*ticker_tasks.values(), return_exceptions=True)
        
        prices = {}
        for i, (name, ticker) in enumerate(zip(ticker_tasks.keys(), tickers)):
            if not isinstance(ticker, Exception) and ticker is not None:
                prices[name] = Decimal(str(ticker['last']))

        ex_names = list(prices.keys())
        for i in range(len(ex_names)):
            for j in range(i+1, len(ex_names)):
                ex_a, ex_b = ex_names[i], ex_names[j]
                price_a, price_b = prices[ex_a], prices[ex_b]
                
                profit1 = calc_profit(price_b, price_a, Decimal('1'))
                profit2 = calc_profit(price_a, price_b, Decimal('1'))
                
                threshold = Decimal(str(user.profit_share_pct)) / Decimal('100')
                
                if profit1 > 0 and (profit1 / (price_a * Decimal('1'))) > threshold:
                    await record_trade(session, user, pair, ex_a, price_a, ex_b, price_b, profit1, simulated=user.mode=='simulate')

                if profit2 > 0 and (profit2 / (price_b * Decimal('1'))) > threshold:
                    await record_trade(session, user, pair, ex_b, price_b, ex_a, price_a, profit2, simulated=user.mode=='simulate')
    
    for wrapper in ex_instances.values():
        await wrapper.close()

async def record_trade(session: Session, user: models.User, pair: str, buy_ex: str, buy_price: Decimal, sell_ex: str, sell_price: Decimal, gross_profit: Decimal, simulated: bool):
    logger.info(f'Potential arbitrage for user {user.telegram_id}: buy on {buy_ex} @ {buy_price}, sell on {sell_ex} @ {sell_price}. Gross profit: {gross_profit}')

    admin_cut = (Decimal(str(user.profit_share_pct)) / Decimal('100')) * gross_profit if gross_profit > 0 else Decimal('0')
    net = gross_profit - admin_cut
    
    trade = models.Trade(
        user_id=user.id,
        pair=pair,
        buy_exchange=buy_ex,
        buy_price=buy_price,
        sell_exchange=sell_ex,
        sell_price=sell_price,
        amount=Decimal('1'),
        gross_profit=gross_profit,
        admin_cut=admin_cut,
        net_profit=net,
        status='simulated' if simulated else 'executed',
        simulated=simulated
    )
    
    session.add(trade)
    session.commit()
    
    if not simulated and admin_cut > 0:
        new_owed = Decimal(str(user.owed_profit)) + admin_cut
        user.owed_profit = new_owed
        session.commit()
        if new_owed > 0:
            user.enabled = False
            session.commit()
            logger.warning(f'User {user.telegram_id} disabled due to outstanding owed profit.')
