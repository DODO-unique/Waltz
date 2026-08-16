from __future__ import annotations

from typing import Any


class WaltzException(Exception):
    """Base exception for all Waltz framework errors."""

    default_code = "WALTZ_ERROR"
    default_severity = "error"

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code or self.default_code
        self.details = details or {}
        self.cause = cause
        super().__init__(message)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "error_code": self.error_code,
            "severity": self.default_severity,
            "details": self.details,
        }


class AuthenticationException(WaltzException):
    """Base exception for all authentication-related errors."""

    default_code = "AUTHENTICATION_ERROR"
    default_severity = "high"


class OIDCTokenInvalidException(AuthenticationException):
    """Raised when an OIDC id_token is structurally invalid or missing required claims."""

    default_code = "OIDC_INVALID"
    default_severity = "critical"


class OAuthProviderException(AuthenticationException):
    """Raised when an OAuth provider rejects or fails a request."""

    default_code = "OAUTH_PROVIDER_ERROR"
    default_severity = "high"


class OAuthNetworkException(AuthenticationException):
    """Raised when a network failure occurs while contacting an OAuth provider."""

    default_code = "OAUTH_NETWORK_ERROR"
    default_severity = "high"


class OAuthStateValidationException(AuthenticationException):
    """Raised when OAuth state validation fails, indicating a possible CSRF issue."""

    default_code = "OAUTH_STATE_INVALID"
    default_severity = "critical"


class CSRFValidationException(OAuthStateValidationException):
    """Backward-compatible alias for OAuth state validation failures."""

    default_code = "CSRF_VALIDATION_FAILED"
    default_severity = "critical"


class UserExistsException(AuthenticationException):
    """Raised when a user already exists during a registration flow."""

    default_code = "USER_EXISTS"
    default_severity = "medium"


class ValidationException(WaltzException):
    """Base exception for input validation failures."""

    default_code = "VALIDATION_ERROR"
    default_severity = "medium"


class UsernameValidationException(ValidationException):
    """Raised when a username violates naming rules."""

    default_code = "INVALID_USERNAME"
    default_severity = "medium"


class PasswordValidationException(ValidationException):
    """Raised when a password violates format or security rules."""

    default_code = "INVALID_PASSWORD"
    default_severity = "medium"


class EmailValidationException(ValidationException):
    """Raised when an email address is malformed or rejected."""

    default_code = "INVALID_EMAIL"
    default_severity = "medium"


class RequiredFieldMissingException(ValidationException):
    """Raised when a required input field is missing."""

    default_code = "MISSING_REQUIRED_FIELD"
    default_severity = "high"


class TypeMismatchException(ValidationException):
    """Raised when an input value has an unexpected type."""

    default_code = "TYPE_MISMATCH"
    default_severity = "medium"


class ResourceNotFoundException(WaltzException):
    """Base exception for resource lookup failures."""

    default_code = "RESOURCE_NOT_FOUND"
    default_severity = "high"


class UserNotFoundException(ResourceNotFoundException):
    """Raised when a user cannot be found."""

    default_code = "USER_NOT_FOUND"
    default_severity = "high"


class CredentialsNotFoundException(ResourceNotFoundException):
    """Raised when provider credentials or an equivalent resource is missing."""

    default_code = "CREDENTIALS_NOT_FOUND"
    default_severity = "high"


class ServiceNotRegisteredException(ResourceNotFoundException):
    """Raised when a required service or feature is not registered in the runtime."""

    default_code = "SERVICE_NOT_REGISTERED"
    default_severity = "high"


class ConfigurationException(WaltzException):
    """Base exception for configuration and setup issues."""

    default_code = "CONFIGURATION_ERROR"
    default_severity = "high"


class DuplicateRegistrationException(ConfigurationException):
    """Raised when a duplicate provider/service/operation registration is attempted."""

    default_code = "DUPLICATE_REGISTRATION"
    default_severity = "high"


class MissingConfigurationException(ConfigurationException):
    """Raised when required configuration is absent."""

    default_code = "MISSING_CONFIG"
    default_severity = "high"


class UnsupportedProviderException(ConfigurationException):
    """Raised when a provider is not supported by the system."""

    default_code = "UNSUPPORTED_PROVIDER"
    default_severity = "high"


class SessionException(WaltzException):
    """Base exception for session-management failures."""

    default_code = "SESSION_ERROR"
    default_severity = "high"


class SessionTokenNotFoundException(SessionException):
    """Raised when a session token is missing or invalid."""

    default_code = "SESSION_TOKEN_NOT_FOUND"
    default_severity = "high"


class InvalidInternalStateException(SessionException):
    """Raised when an internal invariant fails due to invalid state."""

    default_code = "INVALID_INTERNAL_STATE"
    default_severity = "critical"


class SecurityException(WaltzException):
    """Base exception for security-related failures."""

    default_code = "SECURITY_ERROR"
    default_severity = "high"


class JWTKeyMissingException(SecurityException):
    """Raised when a JWT verification key cannot be retrieved."""

    default_code = "JWT_KEY_MISSING"
    default_severity = "critical"


class InternalException(WaltzException):
    """Base exception for internal logic errors."""

    default_code = "INTERNAL_ERROR"
    default_severity = "critical"


class DataIntegrityException(InternalException):
    """Raised when data integrity or exception-wrapping logic fails."""

    default_code = "DATA_INTEGRITY_ERROR"
    default_severity = "medium"

class OTPExpiredException(WaltzException):
    """OTP Expired. Raised locally, to be caught."""

    default_code = "OTP_EXPIRED"
    default_severity = "high"

class InvalidProviderNameUsed(WaltzException):
    """Provider name used is not applicable in the relevant field"""

    default_code = "INVALID_PROVIDER"
    default_severity = "high"

__all__ = [
    "AuthenticationException",
    "CSRFValidationException",
    "ConfigurationException",
    "CredentialsNotFoundException",
    "DataIntegrityException",
    "DuplicateRegistrationException",
    "EmailValidationException",
    "InternalException",
    "InvalidInternalStateException",
    "InvalidProviderNameUsed",
    "JWTKeyMissingException",
    "MissingConfigurationException",
    "OAuthNetworkException",
    "OAuthProviderException",
    "OAuthStateValidationException",
    "OIDCTokenInvalidException",
    "OTPExpiredException",
    "PasswordValidationException",
    "RequiredFieldMissingException",
    "ResourceNotFoundException",
    "SecurityException",
    "ServiceNotRegisteredException",
    "SessionException",
    "SessionTokenNotFoundException",
    "TypeMismatchException",
    "UnsupportedProviderException",
    "UserExistsException",
    "UserNotFoundException",
    "UsernameValidationException",
    "ValidationException",
    "WaltzException"
]
