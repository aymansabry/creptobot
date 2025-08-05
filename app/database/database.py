from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import SessionLocal, init_db

class DBSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with SessionLocal() as session:
            data["session"] = session
            return await handler(event, data)

async def setup_database(dp):
    await init_db()
    dp.message.middleware(DBSessionMiddleware())
