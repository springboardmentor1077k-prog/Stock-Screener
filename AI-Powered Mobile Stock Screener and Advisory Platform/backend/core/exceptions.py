# Custom Exceptions for Stock Screener
from fastapi import HTTPException, status


class StockScreenerException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class InvalidQueryException(StockScreenerException):
    def __init__(self, detail: str = "Invalid query format"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class InsufficientDataException(StockScreenerException):
    def __init__(self, detail: str = "Insufficient data for the requested operation"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedAccessException(StockScreenerException):
    def __init__(self, detail: str = "Unauthorized access"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ResourceNotFoundException(StockScreenerException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ValidationException(StockScreenerException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class DatabaseException(StockScreenerException):
    def __init__(self, detail: str = "Database error occurred"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class APIServiceException(StockScreenerException):
    def __init__(self, detail: str = "External API service error"):
        super().__init__(detail=detail, status_code=status.HTTP_502_BAD_GATEWAY)


class RateLimitException(StockScreenerException):
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(detail=detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS)
