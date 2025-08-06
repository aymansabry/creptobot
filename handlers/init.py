from .admin import router as admin_router
from .commands import router as commands_router
from .deals import router as deals_router

__all__ = ['admin_router', 'commands_router', 'deals_router']
