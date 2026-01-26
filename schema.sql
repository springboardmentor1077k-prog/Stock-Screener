CREATE DATABASE IF NOT EXISTS stock_db;
USE stock_db;
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE stocks (
    stock_id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    company_name VARCHAR(100),
    sector VARCHAR(50),
    industry VARCHAR(50),
    exchange VARCHAR(20),
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
    CONSTRAINT fk_fund_stock
        FOREIGN KEY (stock_id)
        REFERENCES stocks(stock_id)
        ON DELETE CASCADE
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
    CONSTRAINT fk_qf_stock
        FOREIGN KEY (stock_id)
        REFERENCES stocks(stock_id)
        ON DELETE CASCADE
);
CREATE TABLE portfolio (
    portfolio_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    stock_id INT,
    quantity INT,
    avg_price DECIMAL(10,2),
    UNIQUE (user_id, stock_id),
    CONSTRAINT fk_port_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_port_stock
        FOREIGN KEY (stock_id)
        REFERENCES stocks(stock_id)
        ON DELETE CASCADE
);
CREATE TABLE alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    stock_id INT,
    alert_type VARCHAR(30),
    trigger_value DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alert_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_alert_stock
        FOREIGN KEY (stock_id)
        REFERENCES stocks(stock_id)
        ON DELETE CASCADE
);
CREATE USER 'stock_user'@'localhost' IDENTIFIED BY 'Stock@123';

GRANT SELECT, INSERT, UPDATE, DELETE
ON stock_db.*
TO 'stock_user'@'localhost';

FLUSH PRIVILEGES;
