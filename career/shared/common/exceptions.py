"""
Common exception classes for all microservices.
"""
from typing import Any, Optional


class ServiceException(Exception):
    """Base exception for all service errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }


class NotFoundException(ServiceException):
    """Resource not found exception."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details or None
        )


class UnauthorizedException(ServiceException):
    """Authentication/Authorization failure exception."""

    def __init__(
        self,
        message: str = "Unauthorized access",
        required_role: Optional[int] = None
    ):
        details = None
        if required_role:
            details = {"required_role_level": required_role}

        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
            details=details
        )


class ForbiddenException(ServiceException):
    """Access forbidden exception."""

    def __init__(
        self,
        message: str = "Access forbidden",
        required_permission: Optional[str] = None
    ):
        details = None
        if required_permission:
            details = {"required_permission": required_permission}

        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
            details=details
        )


class ValidationException(ServiceException):
    """Input validation failure exception."""

    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[list] = None
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"errors": errors} if errors else None
        )


class ConflictException(ServiceException):
    """Resource conflict exception."""

    def __init__(
        self,
        message: str = "Resource conflict",
        conflicting_field: Optional[str] = None
    ):
        details = None
        if conflicting_field:
            details = {"conflicting_field": conflicting_field}

        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details
        )


class ServiceUnavailableException(ServiceException):
    """External service unavailable exception."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service_name: Optional[str] = None,
        retry_after: Optional[int] = None
    ):
        details = {}
        if service_name:
            details["service_name"] = service_name
        if retry_after:
            details["retry_after_seconds"] = retry_after

        super().__init__(
            message=message,
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details=details or None
        )


class RateLimitException(ServiceException):
    """Rate limit exceeded exception."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        details = None
        if retry_after:
            details = {"retry_after_seconds": retry_after}

        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )
