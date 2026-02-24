"""
Error Handling Utilities for Stock Screener Backend

Provides centralized error handling with:
- Custom exception classes with error codes
- Retry decorator for system failures
- Safe database call context manager
- Standardized error response formatting
"""

import functools
import time
import logging
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============= ERROR CODES =============
class ErrorCode:
    """Standardized error codes for API responses."""
    USER_ERROR = "USER_ERROR"          # Validation failures
    SYSTEM_ERROR = "SYSTEM_ERROR"      # DB/Cache/Network issues
    NOT_FOUND = "NOT_FOUND"            # Resource not found
    EDGE_CASE = "EDGE_CASE"            # Logical edge cases handled


# ============= CUSTOM EXCEPTIONS =============
class AppError(Exception):
    """Base application exception with error code."""
    def __init__(self, message: str, error_code: str = ErrorCode.SYSTEM_ERROR, details: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class ValidationError(AppError):
    """Raised when user input validation fails."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, ErrorCode.USER_ERROR, details)


class AppSystemError(AppError):
    """Raised when system-level errors occur (DB, cache, network)."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, ErrorCode.SYSTEM_ERROR, details)


class NotFoundError(AppError):
    """Raised when requested resource is not found."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, ErrorCode.NOT_FOUND, details)


class EdgeCaseError(AppError):
    """Raised when logical edge case is encountered and handled."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, ErrorCode.EDGE_CASE, details)


# ============= ERROR RESPONSE FORMATTER =============
def format_error_response(error: Exception) -> Dict[str, Any]:
    """
    Format exception into standardized API error response.
    
    Args:
        error: Exception to format
        
    Returns:
        Dict with error_code, message, and optional details
    """
    if isinstance(error, AppError):
        return {
            "error_code": error.error_code,
            "message": error.message,
            "details": error.details
        }
    else:
        # Unexpected error - log it and return generic message
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        return {
            "error_code": ErrorCode.SYSTEM_ERROR,
            "message": "An unexpected error occurred",
            "details": "Please try again later"
        }


# ============= RETRY DECORATOR =============
def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function on failure with exponential backoff.
    
    Good for: Database connections, external API calls, network requests
    Bad for: Validation errors, SQL syntax errors, business logic failures
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # Don't retry on validation errors
                    if isinstance(e, ValidationError):
                        raise
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            # All retries exhausted
            raise AppSystemError(
                f"Operation failed after {max_attempts} attempts",
                details=str(last_exception)
            )
        
        return wrapper
    return decorator


# ============= SAFE DATABASE CALL =============
@contextmanager
def safe_db_call(operation_name: str = "Database operation"):
    """
    Context manager for safe database operations with error handling.
    
    Usage:
        with safe_db_call("Fetching portfolios"):
            cursor.execute(query)
            results = cursor.fetchall()
    
    Args:
        operation_name: Description of the operation for logging
    """
    try:
        yield
    except Exception as e:
        logger.error(f"{operation_name} failed: {str(e)}", exc_info=True)
        raise AppSystemError(
            f"{operation_name} failed",
            details="Database connection error. Please try again."
        )


# ============= VALIDATION HELPERS =============
def validate_not_empty(value: str, field_name: str) -> None:
    """Validate that string field is not empty."""
    if not value or not value.strip():
        raise ValidationError(
            f"{field_name} cannot be empty",
            details=f"Please provide a valid {field_name.lower()}"
        )


def validate_positive(value: float, field_name: str) -> None:
    """Validate that numeric field is positive."""
    if value <= 0:
        raise ValidationError(
            f"{field_name} must be greater than 0",
            details=f"Please enter a positive value for {field_name.lower()}"
        )


def validate_non_negative(value: float, field_name: str) -> None:
    """Validate that numeric field is non-negative."""
    if value < 0:
        raise ValidationError(
            f"{field_name} cannot be negative",
            details=f"Please enter a non-negative value for {field_name.lower()}"
        )


def validate_in_list(value: str, allowed_values: list, field_name: str) -> None:
    """Validate that value is in allowed list."""
    if value not in allowed_values:
        raise ValidationError(
            f"Invalid {field_name}: '{value}'",
            details=f"Allowed values: {', '.join(allowed_values)}"
        )


# ============= NULL SAFETY HELPERS =============
def safe_divide(numerator: Optional[float], denominator: Optional[float], default: float = 0.0) -> float:
    """
    Safely divide two numbers, handling None and division by zero.
    
    Args:
        numerator: Numerator value (can be None)
        denominator: Denominator value (can be None)
        default: Default value to return on error
        
    Returns:
        Division result or default value
    """
    try:
        if numerator is None or denominator is None or denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """
    Safely get value from dict with default.
    
    Args:
        data: Dictionary to get value from
        key: Key to lookup
        default: Default value if key not found or value is None
        
    Returns:
        Value from dict or default
    """
    value = data.get(key, default)
    return value if value is not None else default
