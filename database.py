# database.py
import os
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def parse_database_url(url):
    result = urlparse(url)
    return {
        "host": result.hostname,
        "user": result.username,
        "password": result.password,
        "database": result.path.lstrip("/"),
        "port": result.port or 3306,
        "auth_plugin": "mysql_native_password",
    }

db_config = parse_database_url(DATABASE_URL)

def get_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("خطأ في اسم المستخدم أو كلمة المرور")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("قاعدة البيانات غير موجودة")
        else:
            print(err)
        return None

def create_tables():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            binance_api_key VARCHAR(255),
            binance_secret_key VARCHAR(255),
            kucoin_api_key VARCHAR(255),
            kucoin_secret_key VARCHAR(255),
            kucoin_password VARCHAR(255),
            invested_amount FLOAT DEFAULT 0,
            profit FLOAT DEFAULT 0,
            active_platforms JSON NULL,
            is_investing BOOLEAN DEFAULT FALSE
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS owner_wallet (
            id INT PRIMARY KEY CHECK (id = 1),
            wallet_address VARCHAR(255),
            profit_percentage FLOAT DEFAULT 10
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS investment_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT,
            platform VARCHAR(50),
            operation VARCHAR(20),
            amount FLOAT,
            price FLOAT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.close()
        conn.commit()
        conn.close()
