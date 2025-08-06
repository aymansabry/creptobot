import psycopg2
from psycopg2 import pool
from core.config import config
import logging

logger = logging.getLogger(__name__)

class Database:
    __connection_pool = None

    @classmethod
    def initialize(cls):
        try:
            db_params = config.DB_PARAMS
            if not db_params:
                logger.error("DATABASE_URL not configured in environment variables!")
                return

            cls.__connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **db_params
            )
            logger.info("✅ تم الاتصال بقاعدة البيانات بنجاح")
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بقاعدة البيانات: {str(e)}")

    @classmethod
    def get_connection(cls):
        if not cls.__connection_pool:
            cls.initialize()
        return cls.__connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        if cls.__connection_pool:
            cls.__connection_pool.putconn(connection)

    @classmethod
    def close_all_connections(cls):
        if cls.__connection_pool:
            cls.__connection_pool.closeall()

# Initialize on import
Database.initialize()
