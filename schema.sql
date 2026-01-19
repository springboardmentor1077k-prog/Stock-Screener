CREATE DATABASE IF NOT EXISTS stock_db;
USE stock_db;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE stocks (
    stock_id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(100),
    sector VARCHAR(50),
    industry VARCHAR(50),
    exchange VARCHAR(20)
);

CREATE TABLE fundamentals (
    fundamental_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT UNIQUE,
    pe_ratio DECIMAL(10,2),
    eps DECIMAL(10,2),
    market_cap BIGINT,
    roe DECIMAL(5,2),
    debt_equity DECIMAL(5,2),
    updated_at TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id) ON DELETE CASCADE
);

CREATE TABLE quarterly_finance (
    qf_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT,
    quarter VARCHAR(5),
    year INT,
    revenue BIGINT,
    ebitda BIGINT,
    net_profit BIGINT,
    UNIQUE (stock_id, quarter, year),
    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id) ON DELETE CASCADE
);

CREATE TABLE portfolio (
    portfolio_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    stock_id INT,
    quantity INT,
    avg_price DECIMAL(10,2),
    UNIQUE (user_id, stock_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
);

CREATE TABLE alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    stock_id INT,
    alert_type VARCHAR(30),
    trigger_value DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
);
