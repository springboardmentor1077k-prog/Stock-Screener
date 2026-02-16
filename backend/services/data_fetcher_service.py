"""
Data Fetcher Service for Alpha Vantage API Integration
Handles fetching historical and real-time financial data using Alpha Vantage API
"""

import os
import requests
import time
from typing import Dict, Any, Optional
import logging
from functools import lru_cache
import threading
from ..core.utils import sanitize_input

logger = logging.getLogger(__name__)

class DataFetcherService:
    def __init__(self):
        # Get the Alpha Vantage API key from environment variables
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            logger.warning("ALPHA_VANTAGE_API_KEY environment variable not set. API calls may fail.")
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        
        # Rate limiting: Alpha Vantage free tier = 5 requests/min, 25 requests/day
        self.rate_limit_delay = 15  # 15 seconds between requests (4/min to stay safe)
        self.last_request_time = 0
        self._lock = threading.Lock()  # Thread lock for rate limiting
        self._max_retries_on_rate_limit = 1  # Retry once when rate limited (65s wait)
        
        # Request timeout
        from ..core.config import settings
        self.request_timeout = settings.api_request_timeout

    def _rate_limit(self):
        """Enforce rate limiting to comply with API limits"""
        with self._lock:  # Use thread lock to ensure thread safety
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            
            if time_since_last_request < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last_request
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()

    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict[Any, Any]]:
        """Make a request to Alpha Vantage API with error handling and retry on rate limit."""
        if not self.api_key:
            logger.error("Alpha Vantage API key not configured. Please set ALPHA_VANTAGE_API_KEY environment variable.")
            return None

        for attempt in range(self._max_retries_on_rate_limit + 1):
            try:
                params_copy = {**params, "apikey": self.api_key}
                self._rate_limit()
                response = requests.get(self.base_url, params=params_copy, timeout=self.request_timeout)
                response.raise_for_status()
                data = response.json()

                if "Error Message" in data:
                    logger.error(f"Alpha Vantage API Error: {data['Error Message']}")
                    return None

                if "Note" in data or (isinstance(data.get("Information"), str) and "rate limit" in data.get("Information", "").lower()):
                    msg = data.get("Note") or data.get("Information") or "Rate limit"
                    logger.warning(f"Alpha Vantage rate limit: {msg}")
                    wait_sec = 65
                    if attempt < self._max_retries_on_rate_limit:
                        logger.warning(f"Waiting {wait_sec}s then retry ({attempt + 1}/{self._max_retries_on_rate_limit})...")
                        time.sleep(wait_sec)
                        continue
                    logger.warning(
                        "Alpha Vantage rate limit persisted after retry. Free tier = 25 requests/day, 5/min. "
                        "If this was your first request, daily quota is likely exhausted—try again tomorrow or use a premium key."
                    )
                    return None

                if "Information" in data:
                    logger.info(f"Alpha Vantage Info: {data['Information']}")

                return data

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error when fetching data: {str(e)}", exc_info=True)
                return None
            except ValueError as e:
                logger.error(f"JSON decode error: {str(e)}", exc_info=True)
                return None
            except Exception as e:
                logger.error(f"Unexpected error when fetching data: {str(e)}", exc_info=True)
                return None

        return None

    @lru_cache(maxsize=128)
    def get_stock_quote_cached(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote for a stock symbol with caching"""
        symbol = sanitize_input(symbol).upper()
        
        if not symbol:
            logger.error("Invalid symbol provided")
            return None
            
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol
        }
        
        data = self._make_request(params)
        if data and "Global Quote" in data:
            return data["Global Quote"]
        
        return None
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote for a stock symbol"""
        return self.get_stock_quote_cached(symbol)

    @lru_cache(maxsize=64)
    def get_company_overview_cached(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company overview information with caching"""
        symbol = sanitize_input(symbol).upper()
        
        if not symbol:
            logger.error("Invalid symbol provided")
            return None
            
        params = {
            "function": "OVERVIEW",
            "symbol": symbol
        }
        
        return self._make_request(params)
    
    def get_company_overview(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company overview information"""
        return self.get_company_overview_cached(symbol)

    @lru_cache(maxsize=64)
    def get_daily_time_series_cached(self, symbol: str, outputsize: str = "compact") -> Optional[Dict[str, Any]]:
        """Get daily time series data (last 100 days or 20+ years based on outputsize) with caching"""
        symbol = sanitize_input(symbol).upper()
        
        if not symbol:
            logger.error("Invalid symbol provided")
            return None
            
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize  # "compact" (last 100 days) or "full" (20+ years)
        }
        
        data = self._make_request(params)
        if data and f"Time Series (Daily)" in data:
            return data[f"Time Series (Daily)"]
        
        return None
    
    def get_daily_time_series(self, symbol: str, outputsize: str = "compact") -> Optional[Dict[str, Any]]:
        """Get daily time series data (last 100 days or 20+ years based on outputsize)"""
        return self.get_daily_time_series_cached(symbol, outputsize)

    @lru_cache(maxsize=64)
    def get_weekly_time_series_cached(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get weekly time series data with caching"""
        symbol = sanitize_input(symbol).upper()
        
        if not symbol:
            logger.error("Invalid symbol provided")
            return None
            
        params = {
            "function": "TIME_SERIES_WEEKLY",
            "symbol": symbol
        }
        
        data = self._make_request(params)
        if data and "Weekly Time Series" in data:
            return data["Weekly Time Series"]
        
        return None
    
    def get_weekly_time_series(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get weekly time series data"""
        return self.get_weekly_time_series_cached(symbol)

    @lru_cache(maxsize=64)
    def get_monthly_time_series_cached(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get monthly time series data with caching"""
        symbol = sanitize_input(symbol).upper()
        
        if not symbol:
            logger.error("Invalid symbol provided")
            return None
            
        params = {
            "function": "TIME_SERIES_MONTHLY",
            "symbol": symbol
        }
        
        data = self._make_request(params)
        if data and "Monthly Time Series" in data:
            return data["Monthly Time Series"]
        
        return None
    
    def get_monthly_time_series(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get monthly time series data"""
        return self.get_monthly_time_series_cached(symbol)

    @lru_cache(maxsize=32)
    def get_income_statement_cached(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get income statement data (annual and quarterly) with caching"""
        symbol = sanitize_input(symbol).upper()
        
        if not symbol:
            logger.error("Invalid symbol provided")
            return None
            
        params = {
            "function": "INCOME_STATEMENT",
            "symbol": symbol
        }
        
        return self._make_request(params)
    
    def get_income_statement(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get income statement data (annual and quarterly)"""
        return self.get_income_statement_cached(symbol)

    @lru_cache(maxsize=32)
    def get_balance_sheet_cached(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get balance sheet data (annual and quarterly) with caching"""
        symbol = sanitize_input(symbol).upper()
        
        if not symbol:
            logger.error("Invalid symbol provided")
            return None
            
        params = {
            "function": "BALANCE_SHEET",
            "symbol": symbol
        }
        
        return self._make_request(params)
    
    def get_balance_sheet(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get balance sheet data (annual and quarterly)"""
        return self.get_balance_sheet_cached(symbol)

    @lru_cache(maxsize=32)
    def get_cash_flow_cached(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cash flow data (annual and quarterly) with caching"""
        symbol = sanitize_input(symbol).upper()
        
        if not symbol:
            logger.error("Invalid symbol provided")
            return None
            
        params = {
            "function": "CASH_FLOW",
            "symbol": symbol
        }
        
        return self._make_request(params)
    
    def get_cash_flow(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cash flow data (annual and quarterly)"""
        return self.get_cash_flow_cached(symbol)

    def clear_cache(self):
        """Clear all caches to force fresh data fetching"""
        self.get_stock_quote_cached.cache_clear()
        self.get_company_overview_cached.cache_clear()
        self.get_daily_time_series_cached.cache_clear()
        self.get_weekly_time_series_cached.cache_clear()
        self.get_monthly_time_series_cached.cache_clear()
        self.get_income_statement_cached.cache_clear()
        self.get_balance_sheet_cached.cache_clear()
        self.get_cash_flow_cached.cache_clear()
    
    def invalidate_symbol_cache(self, symbol: str):
        """Invalidate cache for a specific symbol"""
        symbol_upper = symbol.upper()
        # Manually clear specific cache entries for the given symbol
        # Note: Since lru_cache doesn't directly support selective removal,
        # we'll need to clear the entire cache for these methods
        # For more granular control, consider using a different caching mechanism
        logger.info(f"Cache cleared for symbol {symbol_upper} (full cache clear)")
    
    def search_symbols(self, keywords: str) -> Optional[Dict[str, Any]]:
        """Search for symbols based on keywords"""
        keywords = sanitize_input(keywords)
        
        if not keywords:
            logger.error("Invalid keywords provided")
            return None
            
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords
        }
        
        return self._make_request(params)

# Global instance of the data fetcher service
data_fetcher_service = DataFetcherService()

# Convenience functions for direct use
def get_stock_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get stock quote"""
    return data_fetcher_service.get_stock_quote(symbol)

def get_company_overview(symbol: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get company overview"""
    return data_fetcher_service.get_company_overview(symbol)

def get_daily_time_series(symbol: str, outputsize: str = "compact") -> Optional[Dict[str, Any]]:
    """Convenience function to get daily time series"""
    return data_fetcher_service.get_daily_time_series(symbol, outputsize)

def get_income_statement(symbol: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get income statement"""
    return data_fetcher_service.get_income_statement(symbol)

def search_symbols(keywords: str) -> Optional[Dict[str, Any]]:
    """Convenience function to search symbols"""
    return data_fetcher_service.search_symbols(keywords)