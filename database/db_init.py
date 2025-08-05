import asyncpg
from config.config import Config

async def init_db():
    conn = await asyncpg.connect(
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        host=Config.DB_HOST,
        port=Config.DB_PORT
    )
    
    await conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        first_name TEXT NOT NULL,
        last_name TEXT,
        join_date TIMESTAMP NOT NULL,
        balance NUMERIC(15, 2) DEFAULT 0.0,
        is_active BOOLEAN DEFAULT TRUE
    );
    
    CREATE TABLE IF NOT EXISTS investment_opportunities (
        id VARCHAR(20) PRIMARY KEY,
        base_currency VARCHAR(10) NOT NULL,
        target_currency VARCHAR(10) NOT NULL,
        buy_market VARCHAR(50) NOT NULL,
        sell_market VARCHAR(50) NOT NULL,
        expected_profit NUMERIC(5, 2) NOT NULL,
        duration_minutes INTEGER NOT NULL,
        timestamp TIMESTAMP NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS trades (
        trade_id VARCHAR(30) PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id),
        opportunity_id VARCHAR(20) REFERENCES investment_opportunities(id),
        amount NUMERIC(15, 2) NOT NULL,
        status VARCHAR(20) NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP,
        profit NUMERIC(15, 2),
        commission NUMERIC(15, 2)
    );
    
    CREATE TABLE IF NOT EXISTS wallets (
        user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
        address VARCHAR(100) NOT NULL,
        balance NUMERIC(15, 2) DEFAULT 0.0,
        last_updated TIMESTAMP
    );
    ''')
    
    await conn.close()
