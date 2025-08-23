import asyncio
from exchange.binance_client import BinanceClient
from core.market import Market
from core.paths import build_graph, find_cycles, invert_route
from core.pricing import simulate_route
from core.risk import Risk
from core.executor import Executor
from db.session import AsyncSessionLocal
from db.models import Opportunity, Trade, FeeLedger, AccountSetting, ApiKey, User
from config import settings
from telegram_bot.notifier import send_user_message
from core.ai_assist import summarize_market
import sqlalchemy

class UserOrchestrator:
    def __init__(self, user_id, api_key, api_secret, trade_amount):
        self.user_id = user_id
        self.client = BinanceClient(api_key, api_secret)
        self.market = Market(self.client)
        self.markets = self.market.markets
        self.graph = build_graph(self.markets)
        self.risk = Risk(self.markets)
        self.executor = Executor(self.markets, api_key, api_secret)
        self.trade_amount = min(trade_amount, settings.max_invest_usd)

    def get_price(self, symbol, side):
        return self.market.best_price(symbol, is_buy=(side=='buy'))

    async def scan_and_execute_once(self):
        routes = []
        for L in (3,4,5):
            routes += find_cycles(self.graph, start='USDT', max_len=L)
        scored = []
        for r in routes:
            sim = simulate_route(r, self.get_price)
            if not sim:
                continue
            gross, net = sim
            scored.append({"route": r, "gross_pct": gross, "net_pct": net, "length": len(r)})
            if net < 0:
                inv = invert_route(r)
                sim2 = simulate_route(inv, self.get_price)
                if sim2:
                    g2,n2 = sim2
                    scored.append({"route": inv, "gross_pct": g2, "net_pct": n2, "length": len(inv), "inverted": True})
        good = [s for s in scored if s['net_pct'] >= settings.min_expected_profit_pct]
        good.sort(key=lambda x: x['net_pct'], reverse=True)
        good = good[:settings.max_concurrent_routes]

        results = []
        async with AsyncSessionLocal() as session:
            for s in scored:
                opp = Opportunity(user_id=self.user_id, length=s['length'], route=str([x[0] for x in s['route']]), expected_gross_pct=s['gross_pct'], expected_net_pct=s['net_pct'], viable=(s['net_pct']>=settings.min_expected_profit_pct))
                session.add(opp)
            await session.commit()

            for s in good:
                can, reason = self.risk.can_execute(s['route'], self.get_price, self.trade_amount)
                if not can:
                    await send_user_message(self.user_id, f"تم تخطي المسار: {[x[0] for x in s['route']]} السبب: {reason}")
                    continue
                res = self.executor.execute_route(s['route'], self.trade_amount)
                t = Trade(user_id=self.user_id, route=str([x[0] for x in s['route']]), length=s['length'], notional_usdt=self.trade_amount, gross_pct=s['gross_pct'], net_pct=s['net_pct'], status='success' if res.get('ok') else 'failed', details=res)
                session.add(t)
                await session.commit()
                results.append((s,res))
            summary = await summarize_market(scored)
            await send_user_message(self.user_id, f"ملخّص السوق:\n{summary}")
        return results

    async def run_loop(self):
        while True:
            try:
                await self.scan_and_execute_once()
            except Exception as e:
                await send_user_message(self.user_id, f"خطأ في الأوركستريتور: {e}")
            await asyncio.sleep(1.5)
