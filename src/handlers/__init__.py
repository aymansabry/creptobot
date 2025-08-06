from aiogram import Dispatcher
from .client import register_client_handlers
from .admin import register_admin_handlers
from .support import register_support_handlers

async def setup_handlers(dp: Dispatcher):
    register_client_handlers(dp)
    register_admin_handlers(dp)
    register_support_handlers(dp)
