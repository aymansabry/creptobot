# app/middlewares/database.py
from aiogram import Dispatcher
from app.database.session import get_session
from app.utils.database_middleware import DatabaseSessionMiddleware

async def setup_database(dp: Dispatcher):
    dp.update.middleware(DatabaseSessionMiddleware(session_pool=get_session()))
