import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db.session import engine
from db.models import Base, User, ApiKey, AccountSetting
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import AsyncSessionLocal
from config import settings
from core.orchestrator import UserOrchestrator
import sqlalchemy
import contextlib

app = FastAPI()
_loops = {}

class RegisterPayload(BaseModel):
    username: str
    telegram_chat_id: str | None = None

class ApiKeysPayload(BaseModel):
    user_id: int
    api_key: str
    api_secret: str
    can_withdraw: bool = False

class StartPayload(BaseModel):
    user_id: int
    trade_amount_usdt: float

class StopPayload(BaseModel):
    user_id: int

@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get('/market_summary')
async def market_summary():
    # quick scan (single public client) - limited resource usage
    try:
        # use default unauthenticated client to list markets (we reuse a Binance client without keys)
        from exchange.binance_client import BinanceClient
        b = BinanceClient()
        mkts = b.load_markets()
        # simple top opportunities placeholder for speed
        symbols = list(mkts.keys())[:40]
        return "ملخص السوق: عدد أزواج محمّلة: %d" % len(symbols)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post('/register')
async def register(p: RegisterPayload):
    async with AsyncSessionLocal() as session:
        u = User(username=p.username, telegram_chat_id=p.telegram_chat_id)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        a = AccountSetting(user_id=u.id)
        session.add(a)
        await session.commit()
        return {"user_id": u.id}

@app.post('/add_keys')
async def add_keys(p: ApiKeysPayload):
    async with AsyncSessionLocal() as session:
        u = await session.get(User, p.user_id)
        if not u:
            raise HTTPException(404, 'user not found')
        ak = ApiKey(user_id=p.user_id, api_key=p.api_key, api_secret=p.api_secret, can_withdraw=p.can_withdraw)
        session.add(ak)
        await session.commit()
        return {"ok": True}

@app.post('/start')
async def start(p: StartPayload):
    if p.trade_amount_usdt <= 0 or p.trade_amount_usdt > settings.max_invest_usd:
        raise HTTPException(400, 'invalid amount')
    async with AsyncSessionLocal() as session:
        u = await session.get(User, p.user_id)
        if not u:
            raise HTTPException(404, 'user not found')
        q = await session.execute(sqlalchemy.select(ApiKey).where(ApiKey.user_id==p.user_id))
        key = q.scalars().first()
        if not key:
            raise HTTPException(400, 'api keys not found')
        from exchange.binance_client import BinanceClient
        b = BinanceClient(key.api_key, key.api_secret)
        try:
            _ = b.fetch_balance()
        except Exception as e:
            raise HTTPException(400, f'api keys invalid: {e}')
        accq = await session.execute(sqlalchemy.select(AccountSetting).where(AccountSetting.user_id==p.user_id))
        acc = accq.scalars().first()
        acc.trading_amount_usdt = p.trade_amount_usdt
        acc.is_running = True
        await session.commit()
        orch = UserOrchestrator(p.user_id, key.api_key, key.api_secret, p.trade_amount_usdt)
        task = asyncio.create_task(orch.run_loop())
        _loops[p.user_id] = task
        return {"ok": True}

@app.post('/stop')
async def stop(p: StopPayload):
    t = _loops.get(p.user_id)
    if not t:
        raise HTTPException(404, 'not running')
    t.cancel()
    with contextlib.suppress(Exception):
        await t
    _loops.pop(p.user_id, None)
    async with AsyncSessionLocal() as session:
        accq = await session.execute(sqlalchemy.select(AccountSetting).where(AccountSetting.user_id==p.user_id))
        acc = accq.scalars().first()
        if acc:
            acc.is_running = False
            await session.commit()
    return {"ok": True}

@app.get('/report')
async def report(user_id: int = 1):
    # simple aggregated report
    async with AsyncSessionLocal() as session:
        trades = await session.execute(sqlalchemy.select(User).where(User.id==user_id))
        u = trades.scalars().first()
        if not u:
            raise HTTPException(404, 'user not found')
        # fetch last 10 trades
        q = await session.execute(sqlalchemy.text("SELECT * FROM trades WHERE user_id=:uid ORDER BY started_at DESC LIMIT 10"), {'uid': user_id})
        rows = q.fetchall()
        if not rows:
            return 'لا توجد صفقات بعد.'
        lines = [str(dict(row)) for row in rows]
        return "\n".join(lines)
