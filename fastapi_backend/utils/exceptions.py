from typing import Any, Optional
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Any] = None

class AppBaseException(Exception):
    def __init__(self, error_code: str, message: str, details: Optional[Any] = None, status_code: int = 400):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(self.message)

class ValidationException(AppBaseException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(error_code="VALIDATION_ERROR", message=message, details=details, status_code=400)

class ComplianceException(AppBaseException):
    def __init__(self, message: str = "Query rejected by compliance"):
        super().__init__(error_code="unsupported_query", message=message, status_code=400)

class SystemException(AppBaseException):
    def __init__(self, message: str = "System error. Please try again later."):
        super().__init__(error_code="SYSTEM_ERROR", message=message, status_code=500)

class ResourceNotFoundException(AppBaseException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(error_code="NOT_FOUND", message=message, status_code=404)

class DatabaseException(AppBaseException):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(error_code="DATABASE_ERROR", message=message, status_code=500)

class ServiceException(AppBaseException):
    def __init__(self, message: str = "Internal service error"):
        super().__init__(error_code="SERVICE_ERROR", message=message, status_code=500)
