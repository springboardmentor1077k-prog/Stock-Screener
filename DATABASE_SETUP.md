# Database Setup Guide

## Database Schema

### 1. Create Database

```sql
CREATE DATABASE stock_screener;
USE stock_screener;
```

### 2. Create Tables

#### stocks_master
```sql
CREATE TABLE stocks_master (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    exchange VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_sector (sector)
);
```

#### fundamentals
```sql
CREATE TABLE fundamentals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock_id INT NOT NULL,
    pe_ratio DECIMAL(10, 2),
    peg_ratio DECIMAL(10, 2),
    debt DECIMAL(15, 2),
    free_cash_flow DECIMAL(15, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks_master(id) ON DELETE CASCADE,
    INDEX idx_stock_id (stock_id),
    INDEX idx_pe_ratio (pe_ratio)
);
```

#### quarterly_financials
```sql
CREATE TABLE quarterly_financials (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock_id INT NOT NULL,
    quarter VARCHAR(10),
    year INT,
    revenue DECIMAL(15, 2),
    ebitda DECIMAL(15, 2),
    net_profit DECIMAL(15, 2),
    FOREIGN KEY (stock_id) REFERENCES stocks_master(id) ON DELETE CASCADE,
    INDEX idx_stock_id (stock_id),
    INDEX idx_year_quarter (year, quarter)
);
```

#### analyst_targets
```sql
CREATE TABLE analyst_targets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock_id INT NOT NULL,
    target_price_low DECIMAL(10, 2),
    target_price_high DECIMAL(10, 2),
    current_market_price DECIMAL(10, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks_master(id) ON DELETE CASCADE,
    INDEX idx_stock_id (stock_id)
);
```

### 3. Sample Data

```sql
-- Insert sample stock
INSERT INTO stocks_master (symbol, company_name, sector, exchange)
VALUES ('AAPL', 'Apple Inc.', 'IT', 'NASDAQ');

SET @stock_id = LAST_INSERT_ID();

-- Insert fundamentals
INSERT INTO fundamentals (stock_id, pe_ratio, peg_ratio, debt, free_cash_flow)
VALUES (@stock_id, 24.5, 2.1, 120000000000, 95000000000);

-- Insert quarterly financials
INSERT INTO quarterly_financials (stock_id, quarter, year, revenue, ebitda, net_profit)
VALUES 
    (@stock_id, 'Q1', 2024, 90000000000, 32000000000, 23000000000),
    (@stock_id, 'Q2', 2024, 95000000000, 35000000000, 25000000000);

-- Insert analyst targets
INSERT INTO analyst_targets (stock_id, target_price_low, target_price_high, current_market_price)
VALUES (@stock_id, 180.00, 220.00, 195.50);
```

### 4. Verification

```sql
-- Verify setup
SELECT 
    s.symbol,
    s.company_name,
    f.pe_ratio,
    q.revenue,
    a.current_market_price
FROM stocks_master s
LEFT JOIN fundamentals f ON s.id = f.stock_id
LEFT JOIN quarterly_financials q ON s.id = q.stock_id
LEFT JOIN analyst_targets a ON s.id = a.stock_id
LIMIT 5;
```

## Performance Optimization

### Recommended Indexes

```sql
-- Additional indexes for common queries
CREATE INDEX idx_fundamentals_pe ON fundamentals(pe_ratio);
CREATE INDEX idx_fundamentals_debt ON fundamentals(debt);
CREATE INDEX idx_quarterly_net_profit ON quarterly_financials(net_profit);
CREATE INDEX idx_sector ON stocks_master(sector);
```

### Query Optimization Tips

1. **Use EXPLAIN** to analyze query performance:
   ```sql
   EXPLAIN SELECT * FROM stocks_master s
   JOIN fundamentals f ON s.id = f.stock_id
   WHERE f.pe_ratio < 25;
   ```

2. **Analyze tables regularly**:
   ```sql
   ANALYZE TABLE stocks_master, fundamentals, quarterly_financials, analyst_targets;
   ```

3. **Monitor slow queries**:
   ```sql
   SHOW VARIABLES LIKE 'slow_query_log%';
   SET GLOBAL slow_query_log = 'ON';
   ```

## Backup and Maintenance

### Backup Database

```bash
# Full backup
mysqldump -u root -p stock_screener > stock_screener_backup.sql

# Compressed backup
mysqldump -u root -p stock_screener | gzip > stock_screener_backup.sql.gz
```

### Restore Database

```bash
# Restore from backup
mysql -u root -p stock_screener < stock_screener_backup.sql

# Restore compressed backup
gunzip < stock_screener_backup.sql.gz | mysql -u root -p stock_screener
```

## Connection Configuration

Update credentials in `stock-ai-backend/db.py`:

```python
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="your_mysql_user",
        password="your_mysql_password",
        database="stock_screener"
    )
```

> **Security Note**: Use environment variables for production:
> ```python
> import os
> password=os.getenv('MYSQL_PASSWORD')
> ```
