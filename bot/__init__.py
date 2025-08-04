# bot/__init__.py
from .config import Config
from .database import init_db

__all__ = ['Config', 'init_db']
__version__ = '1.0.0'
