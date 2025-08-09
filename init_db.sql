-- init_db.sql
CREATE TABLE IF NOT EXISTS roles (
    id INT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);
INSERT IGNORE INTO roles (id, name) VALUES (1,'Owner'),(2,'Admin'),(3,'User');

CREATE TABLE IF NOT EXISTS platforms (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
INSERT IGNORE INTO platforms (id, name) VALUES (1,'Binance'),(2,'Kucoin');

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    role_id INT NOT NULL,
    api_binance_key VARCHAR(255),
    api_binance_secret VARCHAR(255),
    api_kucoin_key VARCHAR(255),
    api_kucoin_secret VARCHAR(255),
    api_kucoin_pass VARCHAR(255),
    wallet_address VARCHAR(255),
    invested_amount DECIMAL(28,8) DEFAULT 0,
    profit_share_percentage DECIMAL(5,2) DEFAULT 3.00,
    is_active BOOLEAN DEFAULT TRUE,
    demo_mode BOOLEAN DEFAULT FALSE,
    commission_rate FLOAT DEFAULT 0.1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS trades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    platform_id INT,
    trade_type ENUM('buy','sell'),
    asset VARCHAR(20),
    amount DECIMAL(28,8),
    price DECIMAL(28,8),
    profit DECIMAL(28,8),
    commission DECIMAL(28,8),
    status ENUM('pending','completed','failed'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (platform_id) REFERENCES platforms(id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT
);

CREATE TABLE IF NOT EXISTS two_factor (
    user_id INT PRIMARY KEY,
    secret VARCHAR(64),
    enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(255),
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS arbitrage_schedules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    start_time TIME,
    end_time TIME,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS support_tickets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    subject VARCHAR(255),
    message TEXT,
    status ENUM('open','closed') DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
