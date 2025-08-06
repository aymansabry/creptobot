from .commands import router as commands_router
from .admin import router as admin_router
from .deals import router as deals_router

routers = [
    commands_router,
    admin_router,
    deals_router
]

__all__ = ['routers']
