import asyncio
import asyncpg
from config import POSTGRES_URI
from logger import logger

# اتصال قاعدة البيانات
async def init_db():
    global conn
    conn = await asyncpg.connect(POSTGRES_URI)
    logger.info("✅ تم الاتصال بقاعدة البيانات بنجاح!")

# إغلاق الاتصال
async def close_db():
    await conn.close()
    logger.info("❌ تم إغلاق الاتصال بقاعدة البيانات.")
