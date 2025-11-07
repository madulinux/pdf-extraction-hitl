"""
Custom Exceptions
Application-specific exceptions
"""


class ApplicationError(Exception):
    """Base application error"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Validation error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class AuthenticationError(ApplicationError):
    """Authentication error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class AuthorizationError(ApplicationError):
    """Authorization error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=403)


class NotFoundError(ApplicationError):
    """Resource not found error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ConflictError(ApplicationError):
    """Conflict error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=409)
