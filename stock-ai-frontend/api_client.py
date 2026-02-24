"""
API Client for backend communication.
Handles authentication and stock screening requests.
"""

import requests
import time
from typing import Dict, Any, Tuple
from config import API_BASE_URL


class APIClient:
    """Client for interacting with the Stock Screener backend API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    @staticmethod
    def _safe_json(response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _extract_error_message(response: requests.Response, fallback: str) -> str:
        data = APIClient._safe_json(response)
        return (
            data.get("detail")
            or data.get("message")
            or data.get("error")
            or fallback
        )

    @staticmethod
    def _normalize_list_payload(data: Dict[str, Any], primary_key: str) -> Dict[str, Any]:
        # Standardized contract: count + total + items, while preserving legacy keys.
        items = data.get("items")
        if not isinstance(items, list):
            legacy = data.get(primary_key, [])
            items = legacy if isinstance(legacy, list) else []

        total = data.get("total")
        count = data.get("count")
        resolved_total = total if isinstance(total, int) else len(items)
        resolved_count = count if isinstance(count, int) else resolved_total

        normalized = dict(data)
        normalized["items"] = items
        normalized["total"] = resolved_total
        normalized["count"] = resolved_count
        normalized[primary_key] = items
        return normalized
    
    def login(self, email: str, password: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Authenticate user and get access token.
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Tuple of (success, message, data)
            - success: True if login successful
            - message: Success or error message
            - data: Response data including access_token
        """
        try:
            response = requests.post(
                f"{self.base_url}/login",
                json={"email": email, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                return True, "Login successful", data
            elif response.status_code == 401:
                return False, "Invalid credentials", {}
            else:
                return False, self._extract_error_message(response, f"Login failed with status {response.status_code}"), {}
        
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}", {}
    
    def register(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Register a new user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            response = requests.post(
                f"{self.base_url}/register",
                json={"email": email, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Registration successful!"
            elif response.status_code == 400:
                return False, self._extract_error_message(response, "Registration failed")
            else:
                return False, self._extract_error_message(response, f"Registration failed with status {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def screen_stocks(self, query: str, token: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Execute stock screening query.
        
        Args:
            query: Natural language query for stock screening
            token: Authentication token
        
        Returns:
            Tuple of (success, message, data)
            - success: True if screening successful
            - message: Success or error message
            - data: Response data including count and rows
        """
        try:
            trimmed_query = (query or "").strip()
            if not trimmed_query:
                return False, "Query cannot be empty", {}

            response = requests.post(
                f"{self.base_url}/screen",
                json={"text": trimmed_query},
                headers={"Authorization": token},
                timeout=30
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                data = self._normalize_list_payload(data, "rows")
                if data.get("status") == "success":
                    count = data.get("count", 0)
                    return True, f"Found {count} matching stocks", data
                else:
                    return False, data.get("message", "Query failed"), {}
            elif response.status_code == 400:
                message = self._extract_error_message(response, "Invalid or unsupported query")
                return False, message, {}
            elif response.status_code == 401:
                return False, "Unauthorized. Please login again.", {}
            else:
                return False, self._extract_error_message(response, f"Request failed with status {response.status_code}"), {}
        
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}", {}
    
    def create_alert(
        self,
        portfolio_id: int | None,
        metric: str,
        operator: str,
        threshold: float,
        token: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Create a new database-wide alert.
        
        Args:
            portfolio_id: Optional legacy portfolio ID (ignored by database-wide monitoring)
            metric: Metric to track (pe_ratio, etc.)
            operator: Comparison operator (<, >, etc.)
            threshold: Threshold value
            token: Authentication token
        
        Returns:
            Tuple of (success, message, data)
        """
        try:
            payload = {
                "metric": metric,
                "operator": operator,
                "threshold": threshold
            }
            if portfolio_id is not None:
                payload["portfolio_id"] = portfolio_id

            response = requests.post(
                f"{self.base_url}/alerts",
                json=payload,
                headers={"Authorization": token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                return True, data.get("message", "Alert created"), data
            elif response.status_code == 400:
                return False, self._extract_error_message(response, "Invalid request"), {}
            elif response.status_code == 401:
                return False, "Unauthorized. Please login again.", {}
            else:
                return False, self._extract_error_message(response, f"Request failed with status {response.status_code}"), {}
        
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}", {}
    
    def get_alerts(self, token: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Get all user alerts.
        
        Args:
            token: Authentication token
        
        Returns:
            Tuple of (success, message, data)
        """
        try:
            response = requests.get(
                f"{self.base_url}/alerts",
                headers={"Authorization": token},
                params={"_": int(time.time() * 1000)},
                timeout=10
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                data = self._normalize_list_payload(data, "alerts")
                return True, "Alerts fetched", data
            elif response.status_code == 401:
                return False, "Unauthorized. Please login again.", {}
            else:
                return False, self._extract_error_message(response, f"Request failed with status {response.status_code}"), {}
        
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}", {}
    
    def delete_alert(self, alert_id: int, token: str) -> Tuple[bool, str]:
        """
        Delete an alert.
        
        Args:
            alert_id: Alert ID to delete
            token: Authentication token
        
        Returns:
            Tuple of (success, message)
        """
        try:
            response = requests.delete(
                f"{self.base_url}/alerts/{alert_id}",
                headers={"Authorization": token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                return True, data.get("message", "Alert deleted")
            elif response.status_code == 404:
                return False, self._extract_error_message(response, "Alert not found")
            elif response.status_code == 401:
                return False, "Unauthorized. Please login again."
            else:
                return False, self._extract_error_message(response, f"Request failed with status {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def evaluate_alerts(self, token: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Manually trigger alert evaluation.
        
        Args:
            token: Authentication token
        
        Returns:
            Tuple of (success, message, data)
        """
        try:
            response = requests.post(
                f"{self.base_url}/alerts/evaluate",
                headers={"Authorization": token},
                timeout=30
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                data = self._normalize_list_payload(data, "triggered_alerts")
                return True, data.get("message", "Evaluation complete"), data
            elif response.status_code == 401:
                return False, "Unauthorized. Please login again.", {}
            else:
                return False, self._extract_error_message(response, f"Request failed with status {response.status_code}"), {}
        
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}", {}
    
    def get_stocks(self, token: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Get list of all available stocks."""
        try:
            response = requests.get(
                f"{self.base_url}/stocks",
                headers={"Authorization": token},
                params={"_": int(time.time() * 1000)},
                timeout=10
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                data = self._normalize_list_payload(data, "stocks")
                return True, "Stocks fetched", data
            else:
                return False, self._extract_error_message(response, f"Failed with status {response.status_code}"), {}
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}", {}
    
    def get_portfolios(self, token: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Get all portfolios for the authenticated user."""
        try:
            response = requests.get(
                f"{self.base_url}/portfolios",
                headers={"Authorization": token},
                params={"_": int(time.time() * 1000)},
                timeout=10
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                data = self._normalize_list_payload(data, "portfolios")
                return True, "Portfolios fetched", data
            else:
                return False, self._extract_error_message(response, f"Failed with status {response.status_code}"), {}
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}", {}
    
    def get_portfolio_holdings(self, portfolio_id: int, token: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Get holdings for a specific portfolio."""
        try:
            response = requests.get(
                f"{self.base_url}/portfolios/{portfolio_id}/holdings",
                headers={"Authorization": token},
                params={"_": int(time.time() * 1000)},
                timeout=10
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                data = self._normalize_list_payload(data, "holdings")
                return True, "Holdings fetched", data
            else:
                return False, self._extract_error_message(response, f"Failed with status {response.status_code}"), {}
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}", {}
    
    def add_to_portfolio(
        self,
        portfolio_id: int,
        stock_symbol: str,
        quantity: int,
        token: str
    ) -> Tuple[bool, str]:
        """Add a stock to a portfolio. Price is auto-fetched from database."""
        try:
            response = requests.post(
                f"{self.base_url}/portfolios/holdings",
                json={
                    "portfolio_id": portfolio_id,
                    "stock_symbol": stock_symbol,
                    "quantity": quantity
                },
                headers={"Authorization": token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                return True, data.get("message", "Stock added")
            else:
                return False, self._extract_error_message(response, "Failed to add stock")
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def remove_from_portfolio(self, holding_id: int, token: str) -> Tuple[bool, str]:
        """Remove a stock from a portfolio."""
        try:
            response = requests.delete(
                f"{self.base_url}/portfolios/holdings/{holding_id}",
                headers={"Authorization": token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = self._safe_json(response)
                return True, data.get("message", "Stock removed")
            else:
                return False, self._extract_error_message(response, "Failed to remove stock")
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
