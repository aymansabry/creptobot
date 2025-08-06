from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from config import config

# تعديل URL لقاعدة البيانات ليتوافق مع Railway
DB_URL = config.DB_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DB_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
