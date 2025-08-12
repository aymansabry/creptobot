# database.py
import os
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')


def parse_database_url(url):
    result = urlparse(url)
    return {
        'host': result.hostname,
        'user': result.username,
        'password': result.password,
        'database': result.path.lstrip('/'),
        'port': result.port or 3306,
        'auth_plugin': 'mysql_native_password'
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
                invested_amount FLOAT DEFAULT 0,
                profit FLOAT DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS platforms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                telegram_id BIGINT,
                platform_name VARCHAR(50),
                api_key VARCHAR(255),
                secret_key VARCHAR(255),
                password VARCHAR(255),
                active BOOLEAN DEFAULT TRUE,
                UNIQUE(telegram_id, platform_name)
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_tables()