import os
import mysql.connector
from mysql.connector import Error

# قراءة رابط قاعدة البيانات من المتغير البيئي
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:pass@localhost:3306/dbname")

# استخراج بيانات الاتصال من DATABASE_URL
def parse_database_url(url):
    if not url.startswith("mysql"):
        raise ValueError("DATABASE_URL يجب أن يكون بصيغة MySQL")
    url = url.replace("mysql+mysqlconnector://", "").replace("mysql://", "")
    user_pass, host_db = url.split("@")
    user, password = user_pass.split(":")
    host_port, dbname = host_db.split("/")
    if ":" in host_port:
        host, port = host_port.split(":")
        port = int(port)
    else:
        host = host_port
        port = 3306
    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "database": dbname
    }

db_config = parse_database_url(DATABASE_URL)

# الاتصال بقاعدة البيانات
def get_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        raise

# إنشاء الجداول إذا لم تكن موجودة
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # جدول الإعدادات
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            k VARCHAR(255) PRIMARY KEY,
            v TEXT
        )
    """)

    # جدول المستخدمين
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            role VARCHAR(50) DEFAULT 'client',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # جدول المحافظ API
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            exchange_name VARCHAR(50),
            api_key TEXT,
            api_secret TEXT,
            active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

# جلب إعداد
def get_setting(key, default=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT v FROM settings WHERE k=%s", (key,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else default

# تعديل أو إضافة إعداد
def set_setting(key, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (k, v) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE v=%s
    """, (key, value, value))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("✅ قاعدة البيانات جاهزة")
