from database import get_db_connection

def init_tables():
    connection = get_db_connection()
    if not connection:
        return

    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        role VARCHAR(20) DEFAULT 'client',
        binance_api_key TEXT,
        binance_api_secret TEXT,
        kucoin_api_key TEXT,
        kucoin_api_secret TEXT,
        kucoin_passphrase TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS investments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        amount FLOAT,
        type VARCHAR(20),
        profit FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS platforms (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        platform_name VARCHAR(50),
        api_key TEXT,
        api_secret TEXT,
        passphrase TEXT
    )
    """)

    connection.commit()
    cursor.close()
    connection.close()
    print("✅ Tables initialized.")

if __name__ == "__main__":
    init_tables()
