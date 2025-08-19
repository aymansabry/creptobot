import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL UNIQUE,
            binance_key TEXT,
            binance_secret TEXT,
            investment_amount FLOAT DEFAULT 0,
            live_mode BOOLEAN DEFAULT FALSE,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            symbol TEXT,
            entry_price FLOAT,
            exit_price FLOAT,
            quantity FLOAT,
            entry_time DATETIME,
            exit_time DATETIME,
            profit FLOAT,
            profit_percentage FLOAT,
            status TEXT DEFAULT 'closed'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            date DATE NOT NULL,
            total_profit FLOAT DEFAULT 0,
            trades_count INT DEFAULT 0,
            successful_trades INT DEFAULT 0
        )
    """)

    db.commit()