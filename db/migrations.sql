CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    api_exchange JSONB,
    trade_limit NUMERIC DEFAULT 100,
    mode TEXT DEFAULT 'simulate', -- 'simulate' or 'live'
    profit_share_pct NUMERIC DEFAULT 10,
    owed_profit NUMERIC DEFAULT 0,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    pair TEXT,
    buy_exchange TEXT,
    buy_price NUMERIC,
    sell_exchange TEXT,
    sell_price NUMERIC,
    amount NUMERIC,
    gross_profit NUMERIC,
    admin_cut NUMERIC,
    net_profit NUMERIC,
    status TEXT, -- 'simulated', 'partially_executed', 'executed', 'failed'
    simulated BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
