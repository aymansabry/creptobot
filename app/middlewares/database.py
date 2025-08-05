# app/middlewares/database.py
from aiogram import Dispatcher
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database.session import engine

session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def setup_database(dp: Dispatcher):
    async def on_startup(dispatcher: Dispatcher):
        pass  # يمكن إضافة منطق تهيئة الجداول هنا لاحقاً إذا لزم الأمر

    dp.startup.register(on_startup)
