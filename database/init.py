from urllib.parse import quote_plus
from config import config

# تعديل رابط PostgreSQL ليتوافق مع Railway
if "postgresql://" in config.DB_URL:
    DB_URL = config.DB_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    DB_URL = f"postgresql+asyncpg://{quote_plus(config.DB_URL)}"
    
engine = create_async_engine(DB_URL)
