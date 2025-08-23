# db.py
import mysql.connector
import logging

logger = logging.getLogger(__name__)

# Replace with your actual database credentials
DB_HOST = "localhost"
DB_USER = "your_user"
DB_PASSWORD = "your_password"
DB_NAME = "trading_bot_db"

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as e:
        logger.error(f"Error connecting to MySQL database: {e}")
        return None

def create_tables():
    """Creates necessary tables if they don't exist."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                api_key VARCHAR(255),
                api_secret VARCHAR(255),
                amount DECIMAL(10, 2)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                pair VARCHAR(50),
                profit DECIMAL(10, 6),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.commit()
        logger.info("Tables created or already exist.")
    except mysql.connector.Error as e:
        logger.error(f"Error creating tables: {e}")
    finally:
        cursor.close()
        conn.close()

def create_user(user_id):
    """Inserts a new user into the database if they don't exist."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
            conn.commit()
            logger.info(f"User {user_id} created in the database.")
        else:
            logger.info(f"User {user_id} already exists.")
    except mysql.connector.Error as e:
        logger.error(f"Error creating user: {e}")
    finally:
        cursor.close()
        conn.close()

def save_api_keys(user_id, api_key, api_secret):
    """Saves API keys for a user."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET api_key = %s, api_secret = %s WHERE user_id = %s",
            (api_key, api_secret, user_id)
        )
        conn.commit()
        logger.info(f"API keys saved for user {user_id}.")
    except mysql.connector.Error as e:
        logger.error(f"Error saving API keys: {e}")
    finally:
        cursor.close()
        conn.close()

def get_user_api_keys(user_id):
    """Retrieves API keys for a user."""
    conn = get_db_connection()
    if not conn:
        return {}
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT api_key, api_secret FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result if result else {}
    except mysql.connector.Error as e:
        logger.error(f"Error getting API keys: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def save_amount(user_id, amount):
    """Saves the trading amount for a user."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET amount = %s WHERE user_id = %s", (amount, user_id))
        conn.commit()
        logger.info(f"Amount {amount} saved for user {user_id}.")
    except mysql.connector.Error as e:
        logger.error(f"Error saving amount: {e}")
    finally:
        cursor.close()
        conn.close()

def get_amount(user_id):
    """Retrieves the trading amount for a user."""
    conn = get_db_connection()
    if not conn:
        return 0.0
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT amount FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0.0
    except mysql.connector.Error as e:
        logger.error(f"Error getting amount: {e}")
        return 0.0
    finally:
        cursor.close()
        conn.close()

def save_last_trades(user_id, pair, profit, timestamp):
    """Saves the last trade details for a user."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO trades (user_id, pair, profit, timestamp) VALUES (%s, %s, %s, %s)",
            (user_id, pair, profit, timestamp)
        )
        conn.commit()
        logger.info(f"Trade for user {user_id} saved.")
    except mysql.connector.Error as e:
        logger.error(f"Error saving trade: {e}")
    finally:
        cursor.close()
        conn.close()

def get_last_trades(user_id):
    """Retrieves the last recorded trades for a user."""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT pair, profit, timestamp FROM trades WHERE user_id = %s ORDER BY timestamp DESC LIMIT 10", (user_id,))
        return cursor.fetchall()
    except mysql.connector.Error as e:
        logger.error(f"Error getting trades: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_tables()