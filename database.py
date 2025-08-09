# database.py
import mysql.connector
import os
from mysql.connector import pooling

DB_POOL = None

def init_pool():
    global DB_POOL
    if DB_POOL is None:
        DB_POOL = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=int(os.getenv("MYSQL_POOL_SIZE", "5")),
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
            autocommit=True
        )

def get_conn():
    if DB_POOL is None:
        init_pool()
    return DB_POOL.get_connection()

def query(sql, params=None, fetchone=False):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    result = cursor.fetchone() if fetchone else cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def execute(sql, params=None):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    conn.commit()
    cursor.close()
    conn.close()
