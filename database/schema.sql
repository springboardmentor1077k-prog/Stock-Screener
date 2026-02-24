-- Main Stocks Table (populated with 500 IT sector stocks)
CREATE TABLE stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(100),
    sector VARCHAR(50),              -- "Information Technology"
    sub_sector VARCHAR(50),          -- Semiconductor, Software, Hardware, Telecom, Cloud, etc.
    price DECIMAL(10, 2),
    change_pct DECIMAL(5, 2),
    pe_ratio DECIMAL(10, 2),
    market_cap DECIMAL(20, 2),
    promoter_holding DECIMAL(5, 2),
    has_buyback BOOLEAN DEFAULT FALSE,
    revenue_growth DECIMAL(5, 2),
    
    -- Quarterly earnings
    q1_earnings DECIMAL(15, 2),
    q2_earnings DECIMAL(15, 2),
    q3_earnings DECIMAL(15, 2),
    q4_earnings DECIMAL(15, 2),
    eps DECIMAL(10, 2),
    dividend_yield DECIMAL(5, 2),
    debt_to_equity DECIMAL(5, 2),
    roe DECIMAL(5, 2),
    exchange VARCHAR(10),
    
    -- PEG & Growth metrics
    peg_ratio DECIMAL(5, 2),            -- PE / Earnings Growth (< 3 is attractive)
    earnings_growth_rate DECIMAL(5, 2), -- Annual earnings growth %
    
    -- Debt & Cash Flow
    free_cash_flow DECIMAL(15, 2),      -- Annual FCF in millions
    total_debt DECIMAL(15, 2),          -- Total debt in millions
    debt_to_fcf DECIMAL(5, 2),          -- Debt/FCF ratio (< 4 means can repay in 4 years)
    
    -- Analyst Price Targets
    analyst_price_low DECIMAL(10, 2),
    analyst_price_high DECIMAL(10, 2),
    analyst_price_avg DECIMAL(10, 2),
    price_vs_target VARCHAR(20),        -- "Below Low", "Near Low", "Mid Range", "Near High", "Above High"
    
    -- Revenue & EBITDA Growth
    revenue_growth_yoy DECIMAL(5, 2),   -- Year over year revenue growth %
    ebitda DECIMAL(15, 2),              -- EBITDA in millions
    ebitda_growth_yoy DECIMAL(5, 2),    -- Year over year EBITDA growth %
    
    -- Earnings Estimates
    estimated_eps DECIMAL(10, 2),       -- Analyst EPS estimate for next quarter
    historical_beat_rate DECIMAL(5, 2), -- % of times company beat estimates (0-100)
    likely_to_beat BOOLEAN DEFAULT FALSE,
    
    -- Earnings Calendar
    next_earnings_date DATE,
    earnings_within_30_days BOOLEAN DEFAULT FALSE
);

-- Alerts Table for Price Alert Management
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) REFERENCES stocks(symbol),
    metric VARCHAR(50), -- e.g., 'P/E Ratio', 'Current Price'
    condition VARCHAR(5), -- '<', '>', '<='
    threshold DECIMAL(15, 2),
    status VARCHAR(20) DEFAULT 'Active',
    triggered_count INTEGER DEFAULT 0
);

-- Portfolio Table
CREATE TABLE portfolio (
    id SERIAL PRIMARY KEY,
    portfolio_name VARCHAR(50), -- e.g., 'md', 'abc'
    symbol VARCHAR(10) REFERENCES stocks(symbol),
    shares INTEGER,
    avg_buy_price DECIMAL(10, 2)
);