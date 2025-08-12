# database.py
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "trading_bot")

def create_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        if connection.is_connected():
            print("✅ متصل بقاعدة البيانات MySQL")
        return connection
    except Error as e:
        print(f"❌ خطأ في الاتصال بـ MySQL: {e}")
        return None

def init_database():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()

        # إنشاء قاعدة البيانات إذا لم تكن موجودة
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")

        # جدول المستخدمين
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            role VARCHAR(20) DEFAULT 'client',
            balance FLOAT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # جدول منصات التداول
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS platforms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            platform_name VARCHAR(50) NOT NULL,
            api_key TEXT,
            api_secret TEXT,
            password TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # جدول الاستثمارات
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS investments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            amount FLOAT NOT NULL,
            type ENUM('virtual', 'real') NOT NULL,
            buy_symbol VARCHAR(20),
            sell_symbol VARCHAR(20),
            profit FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # جدول تحليلات السوق
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_analysis (
            id INT AUTO_INCREMENT PRIMARY KEY,
            analysis_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        connection.commit()
        cursor.close()
        connection.close()
        print("✅ تم إنشاء الجداول بنجاح")

if __name__ == "__main__":
    init_database()
