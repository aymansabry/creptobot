CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    wallet_balance FLOAT DEFAULT 0,
    investment_amount FLOAT DEFAULT 0,
    profit_earned FLOAT DEFAULT 0,
    trading_mode VARCHAR(50) DEFAULT 'demo',
    active BOOLEAN DEFAULT TRUE,
    encrypted_binance_api_key TEXT,
    encrypted_binance_api_secret TEXT,
    encrypted_kucoin_api_key TEXT,
    encrypted_kucoin_api_secret TEXT,
    encrypted_kucoin_api_passphrase TEXT,
    commission_rate FLOAT DEFAULT 0.01, -- نسبة العمولة (1%)
    commission_accepted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    platform VARCHAR(255),
    balance FLOAT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    trade_type VARCHAR(255),
    amount FLOAT,
    profit FLOAT,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
