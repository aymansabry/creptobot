# db.py
import asyncio
import logging
import os
from urllib.parse import urlparse
import aiomysql

logger = logging.getLogger(__name__)

# ====== إعدادات الاتصال بقاعدة البيانات - يتم جلبها من متغيرات البيئة تلقائياً ======
DATABASE_URL = os.getenv("DATABASE_URL")

async def get_db_connection():
    """
    تأسيس اتصال غير متزامن بقاعدة بيانات MySQL باستخدام DATABASE_URL.
    """
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable is not set.")
        return None

    try:
        url = urlparse(DATABASE_URL)
        conn = await aiomysql.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            db=url.path[1:],
            port=url.port,
            autocommit=True, # Ensure that the changes are committed instantly
            loop=asyncio.get_event_loop()
        )
        return conn
    except Exception as e:
        logger.error(f"خطأ في الاتصال بقاعدة بيانات MySQL: {e}")
        return None

async def create_tables():
    """
    إنشاء الجداول الضرورية إذا لم تكن موجودة.
    """
    conn = await get_db_connection()
    if not conn:
        return
    
    async with conn.cursor() as cursor:
        try:
            # جدول المستخدمين
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    api_key VARCHAR(255),
                    api_secret VARCHAR(255),
                    amount DECIMAL(10, 2)
                )
            """)
            # جدول الصفقات
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    pair VARCHAR(50),
                    profit DECIMAL(10, 6),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            await conn.commit()
            logger.info("تم إنشاء الجداول بنجاح أو أنها موجودة بالفعل.")
        except Exception as e:
            logger.error(f"خطأ في إنشاء الجداول: {e}")
        finally:
            conn.close()

async def create_user(user_id):
    """
    إضافة مستخدم جديد إلى قاعدة البيانات إذا لم يكن موجودًا.
    """
    conn = await get_db_connection()
    if not conn:
        return
    
    async with conn.cursor() as cursor:
        try:
            await cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            if not await cursor.fetchone():
                await cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
                await conn.commit()
                logger.info(f"تم إنشاء المستخدم {user_id} في قاعدة البيانات.")
            else:
                logger.info(f"المستخدم {user_id} موجود بالفعل.")
        except Exception as e:
            logger.error(f"خطأ في إنشاء المستخدم: {e}")
        finally:
            conn.close()

async def save_api_keys(user_id, api_key, api_secret):
    """
    حفظ مفاتيح API للمستخدم.
    """
    conn = await get_db_connection()
    if not conn:
        return
    
    async with conn.cursor() as cursor:
        try:
            await cursor.execute(
                "UPDATE users SET api_key = %s, api_secret = %s WHERE user_id = %s",
                (api_key, api_secret, user_id)
            )
            await conn.commit()
            logger.info(f"تم حفظ مفاتيح API للمستخدم {user_id}.")
        except Exception as e:
            logger.error(f"خطأ في حفظ مفاتيح API: {e}")
        finally:
            conn.close()

async def get_user_api_keys(user_id):
    """
    استرجاع مفاتيح API للمستخدم.
    """
    conn = await get_db_connection()
    if not conn:
        return {}
    
    async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
            await cursor.execute("SELECT api_key, api_secret FROM users WHERE user_id = %s", (user_id,))
            result = await cursor.fetchone()
            return result if result else {}
        except Exception as e:
            logger.error(f"خطأ في استرجاع مفاتيح API: {e}")
            return {}
        finally:
            conn.close()

async def save_amount(user_id, amount):
    """
    حفظ مبلغ التداول للمستخدم.
    """
    conn = await get_db_connection()
    if not conn:
        return
    
    async with conn.cursor() as cursor:
        try:
            await cursor.execute("UPDATE users SET amount = %s WHERE user_id = %s", (amount, user_id))
            await conn.commit()
            logger.info(f"تم حفظ المبلغ {amount} للمستخدم {user_id}.")
        except Exception as e:
            logger.error(f"خطأ في حفظ المبلغ: {e}")
        finally:
            conn.close()

async def get_amount(user_id):
    """
    استرجاع مبلغ التداول للمستخدم.
    """
    conn = await get_db_connection()
    if not conn:
        return 0.0
    
    async with conn.cursor() as cursor:
        try:
            await cursor.execute("SELECT amount FROM users WHERE user_id = %s", (user_id,))
            result = await cursor.fetchone()
            return result[0] if result and result[0] else 0.0
        except Exception as e:
            logger.error(f"خطأ في استرجاع المبلغ: {e}")
            return 0.0
        finally:
            conn.close()

async def save_last_trades(user_id, pair, profit):
    """
    حفظ تفاصيل آخر صفقة للمستخدم.
    """
    conn = await get_db_connection()
    if not conn:
        return
    
    async with conn.cursor() as cursor:
        try:
            await cursor.execute(
                "INSERT INTO trades (user_id, pair, profit) VALUES (%s, %s, %s)",
                (user_id, pair, profit)
            )
            await conn.commit()
            logger.info(f"تم حفظ الصفقة للمستخدم {user_id}.")
        except Exception as e:
            logger.error(f"خطأ في حفظ الصفقة: {e}")
        finally:
            conn.close()

async def get_last_trades(user_id):
    """
    استرجاع آخر الصفقات المسجلة للمستخدم.
    """
    conn = await get_db_connection()
    if not conn:
        return []
    
    async with conn.cursor(aiomysql.DictCursor) as cursor:
        try:
            await cursor.execute("SELECT pair, profit, timestamp FROM trades WHERE user_id = %s ORDER BY timestamp DESC LIMIT 10", (user_id,))
            return await cursor.fetchall()
        except Exception as e:
            logger.error(f"خطأ في استرجاع الصفقات: {e}")
            return []
        finally:
            conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())