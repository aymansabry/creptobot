from strategy_manager import StrategyManager
from database import SessionLocal
from models import User
from settings import MODE
import time

class ArbEngine:
    def __init__(self):
        self.db = SessionLocal()

    def run_once_for_user(self, user_id: int):
        user = self.db.query(User).filter(User.id==user_id).first()
        if not user:
            return
        # init clients
        from arbitrag_helpers import get_clients_for_user
        clients = get_clients_for_user(user.id)
        if not clients:
            return
        settings = {
            'FEE_ESTIMATE': {'binance':0.001,'bybit':0.001,'okx':0.001},
            'SLIPPAGE_BUFFER': 0.0007,
            'MIN_PROFIT_USDT': 2.0,
        }
        manager = StrategyManager(clients, user, settings)
        manager.execute_best()

    def start_scheduler(self, interval_seconds=30):
        while True:
            users = self.db.query(User).filter(User.role=='client').all()
            for u in users:
                try:
                    self.run_once_for_user(u.id)
                except Exception as e:
                    print('run error', e)
            time.sleep(interval_seconds)
