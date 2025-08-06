from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.config.config import Config

DATABASE_URL = (
    f"postgresql+asyncpg://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@"
    f"{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
