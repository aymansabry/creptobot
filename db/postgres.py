import psycopg2
from psycopg2 import pool
from core.config import Config

class Database:
    __connection_pool = None

    @classmethod
    def initialize(cls):
        cls.__connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 10,
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )

    @classmethod
    def get_connection(cls):
        return cls.__connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        cls.__connection_pool.putconn(connection)

    @classmethod
    def close_all_connections(cls):
        cls.__connection_pool.closeall()

# Initialize on import
Database.initialize()
