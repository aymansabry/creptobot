# database.py
import os
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "crypto_bot")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=DictCursor,
        autocommit=True
    )

def init_db():
    """Create DB if needed tables are missing. Safe to call on startup."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # roles (simple numeric roles could be used instead)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INT PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL
        )""")
        cur.execute("INSERT IGNORE INTO roles (id, name) VALUES (1,'Owner'),(2,'Admin'),(3,'User')")

        # platforms
        cur.execute("""
        CREATE TABLE IF NOT EXISTS platforms (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )""")
        cur.execute("INSERT IGNORE INTO platforms (id, name) VALUES (1,'Binance'),(2,'Kucoin')")

        # users
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            telegram_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(150),
            role_id INT NOT NULL DEFAULT 3,
            api_binance_key VARCHAR(255),
            api_binance_secret VARCHAR(255),
            api_kucoin_key VARCHAR(255),
            api_kucoin_secret VARCHAR(255),
            api_kucoin_pass VARCHAR(255),
            wallet_address VARCHAR(255),
            invested_amount DECIMAL(28,8) DEFAULT 0,
            profit_share_percentage DECIMAL(5,2) DEFAULT 3.00,
            demo_mode BOOLEAN DEFAULT FALSE,
            commission_rate DECIMAL(6,4) DEFAULT 0.1000,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )""")

        # trades
        cur.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT,
            platform_id INT,
            trade_type ENUM('buy','sell'),
            asset VARCHAR(50),
            amount DECIMAL(28,8),
            price DECIMAL(28,8),
            profit DECIMAL(28,8),
            commission DECIMAL(28,8),
            status ENUM('pending','completed','failed'),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (platform_id) REFERENCES platforms(id)
        )""")

        # notifications
        cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT,
            message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        # settings
        cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INT PRIMARY KEY AUTO_INCREMENT,
            setting_key VARCHAR(100) UNIQUE NOT NULL,
            setting_value TEXT
        )""")

        # 2FA
        cur.execute("""
        CREATE TABLE IF NOT EXISTS two_factor (
            user_id INT PRIMARY KEY,
            secret VARCHAR(128),
            enabled BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        # activity logs
        cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT,
            action VARCHAR(255),
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        # schedules
        cur.execute("""
        CREATE TABLE IF NOT EXISTS arbitrage_schedules (
            id INT PRIMARY KEY AUTO_INCREMENT,
            start_time TIME,
            end_time TIME,
            active BOOLEAN DEFAULT TRUE
        )""")

        # support tickets
        cur.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT,
            subject VARCHAR(255),
            message TEXT,
            status ENUM('open','closed') DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

        logger.info("✅ Database initialized and tables are ready.")
    except Exception as e:
        logger.exception("❌ Failed to initialize DB: %s", e)
        raise
    finally:
        if conn:
            conn.close()

# Helper simple query/execute functions
def query(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()

def query_one(sql, params=None):
    res = query(sql, params)
    return res[0] if res else None

def execute(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
    finally:
        conn.close()
