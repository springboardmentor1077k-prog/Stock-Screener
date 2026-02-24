FIELD_REGISTRY = {
    # ---------- stocks_master ----------
    "symbol": {
        "table": "stocks_master",
        "column": "symbol",
        "type": "string",
        "alias": "s",
        "metric_type": "snapshot"
    },
    "company_name": {
        "table": "stocks_master",
        "column": "company_name",
        "type": "string",
        "alias": "s",
        "metric_type": "snapshot"
    },
    "sector": {
        "table": "stocks_master",
        "column": "sector",
        "type": "string",
        "alias": "s",
        "metric_type": "snapshot"
    },
    "exchange": {
        "table": "stocks_master",
        "column": "exchange",
        "type": "string",
        "alias": "s",
        "metric_type": "snapshot"
    },

    # ---------- fundamentals ----------
    "pe_ratio": {
        "table": "fundamentals",
        "column": "pe_ratio",
        "type": "number",
        "alias": "f",
        "metric_type": "snapshot"
    },
    "peg_ratio": {
        "table": "fundamentals",
        "column": "peg_ratio",
        "type": "number",
        "alias": "f",
        "metric_type": "snapshot"
    },
    "debt": {
        "table": "fundamentals",
        "column": "debt",
        "type": "number",
        "alias": "f",
        "metric_type": "snapshot"
    },
    "free_cash_flow": {
        "table": "fundamentals",
        "column": "free_cash_flow",
        "type": "number",
        "alias": "f",
        "metric_type": "snapshot"
    },

    # ---------- quarterly_financials ----------
    "revenue": {
        "table": "quarterly_financials",
        "column": "revenue",
        "type": "number",
        "alias": "q",
        "metric_type": "time_series"
    },
    "ebitda": {
        "table": "quarterly_financials",
        "column": "ebitda",
        "type": "number",
        "alias": "q",
        "metric_type": "time_series"
    },
    "net_profit": {
        "table": "quarterly_financials",
        "column": "net_profit",
        "type": "number",
        "alias": "q",
        "metric_type": "time_series"
    },

    # ---------- analyst_targets ----------
    "target_price_low": {
        "table": "analyst_targets",
        "column": "target_price_low",
        "type": "number",
        "alias": "a",
        "metric_type": "snapshot"
    },
    "target_price_high": {
        "table": "analyst_targets",
        "column": "target_price_high",
        "type": "number",
        "alias": "a",
        "metric_type": "snapshot"
    },
    "current_market_price": {
        "table": "analyst_targets",
        "column": "current_market_price",
        "type": "number",
        "alias": "a",
        "metric_type": "snapshot"
    }
}
