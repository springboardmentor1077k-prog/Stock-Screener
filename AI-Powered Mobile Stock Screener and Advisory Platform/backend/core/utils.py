"""
Core Utilities for Stock Screener
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
import re
import copy
import logging
from fastapi import HTTPException


def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not input_str:
        return ""
    # Remove potentially dangerous characters/sequences
    sanitized = re.sub(r'[;"\'\\<>{}\[\]()`=]', '', input_str)
    # Remove SQL keywords to prevent SQL injection
    sanitized = re.sub(r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT|WAITFOR|DELAY|SLEEP|BENCHMARK)\b', '', sanitized, flags=re.IGNORECASE)
    # Remove potential script tags
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    # Remove potential javascript events
    sanitized = re.sub(r'on\w+\s*=\\?"[^"]*\\?"', '', sanitized, flags=re.IGNORECASE)
    return sanitized.strip()


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def format_currency(value: float, currency: str = "USD") -> str:
    """Format currency values"""
    return f"{currency} {value:,.2f}"


def format_percentage(value: float) -> str:
    """Format percentage values"""
    return f"{value:.2f}%"


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat()


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / abs(old_value)) * 100


def format_financial_metric(metric_name: str, value: float, precision: int = 2) -> Dict[str, Any]:
    """Format financial metrics with appropriate units and labels"""
    formatted_value = round(value, precision)

    if "ratio" in metric_name.lower():
        return {
            "value": formatted_value,
            "unit": "",
            "formatted": f"{formatted_value:.{precision}f}x"
        }
    elif "price" in metric_name.lower() or "value" in metric_name.lower():
        return {
            "value": formatted_value,
            "unit": "$",
            "formatted": f"${formatted_value:,.{precision}f}"
        }
    elif "yield" in metric_name.lower():
        return {
            "value": formatted_value,
            "unit": "%",
            "formatted": f"{formatted_value:.{precision}f}%"
        }
    else:
        return {
            "value": formatted_value,
            "unit": "",
            "formatted": f"{formatted_value:.{precision}f}"
        }


def handle_database_error(error: Exception, operation: str = "database operation"):
    """
    Consistent error handling for database operations.
    
    Args:
        error: The caught exception
        operation: Description of the operation that failed
        
    Raises:
        HTTPException with appropriate status code and user-friendly message
    """
    from sqlalchemy.exc import SQLAlchemyError
    
    if isinstance(error, SQLAlchemyError):
        # Specific database connection error
        raise HTTPException(
            status_code=504, 
            detail="Server timeout - unable to connect to database. Please try again later."
        )
    else:
        # Other unexpected errors
        raise HTTPException(
            status_code=500, 
            detail="Internal server error occurred. Please try again later."
        )


def create_safe_db_operation(operation_func, *args, **kwargs):
    """
    Wrapper to safely execute database operations with consistent error handling.
    
    Args:
        operation_func: The function to execute
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Result of the operation function
    """
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        handle_database_error(e)


def mask_sensitive_data(data: dict, fields_to_mask: list = ["password", "token", "secret", "key"]):
    """
    Mask sensitive fields in data dictionaries for logging purposes.
    
    Args:
        data: Dictionary containing potentially sensitive data
        fields_to_mask: List of field names to mask
        
    Returns:
        Dictionary with sensitive fields masked
    """
    masked_data = copy.deepcopy(data)
    for field in fields_to_mask:
        if field in masked_data:
            if isinstance(masked_data[field], str):
                masked_data[field] = "***MASKED***"
            else:
                masked_data[field] = "***MASKED***"
    return masked_data


logger = logging.getLogger(__name__)


def log_api_call(endpoint: str, method: str, user_id: str = None, status_code: int = None):
    """
    Log API calls for monitoring and analytics.
    
    Args:
        endpoint: API endpoint that was called
        method: HTTP method used
        user_id: ID of the user making the call (if authenticated)
        status_code: HTTP status code of the response
    """
    log_msg = f"API Call: {method} {endpoint}"
    if user_id:
        log_msg += f" by user {user_id}"
    if status_code:
        log_msg += f" - Status: {status_code}"
    logger.info(log_msg)


def create_api_response(success: bool, data=None, message: str = "", error: str = "", status_code: int = 200):
    """
    Create a standardized API response.
    
    Args:
        success: Whether the request was successful
        data: The response data
        message: Success message
        error: Error message (if any)
        status_code: HTTP status code
        
    Returns:
        Dictionary with standardized response format
    """
    response = {
        "success": success,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if success:
        response["data"] = data
        response["message"] = message
    else:
        response["error"] = error
        
    return response