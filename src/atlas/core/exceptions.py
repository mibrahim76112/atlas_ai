"""Application errors. Deliberately free of any HTTP concepts."""


class AppError(Exception):
    """Base class for expected application errors."""

    code = "internal_error"
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class ConflictError(AppError):
    code = "conflict"
    message = "The resource already exists."


class NotFoundError(AppError):
    code = "not_found"
    message = "The resource was not found."


class AuthenticationError(AppError):
    code = "authentication_failed"
    message = "Invalid credentials."


class PermissionDeniedError(AppError):
    code = "permission_denied"
    message = "You do not have access to this resource."


class EmailAlreadyRegisteredError(ConflictError):
    code = "email_already_registered"
    message = "That email address is already registered."
