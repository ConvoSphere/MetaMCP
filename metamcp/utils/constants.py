"""
Constants and Configuration Values

This module contains all constant values used throughout the application
to avoid magic numbers and improve maintainability.
"""

# =============================================================================
# SECURITY CONSTANTS
# =============================================================================

# Password Requirements
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

# Session Management
SESSION_TIMEOUT_MINUTES = 60
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
TOKEN_EXPIRY_MINUTES = 30

# Rate Limiting
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_BURST_MULTIPLIER = 2

# Security Headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# =============================================================================
# DATABASE CONSTANTS
# =============================================================================

# Connection Pool
DEFAULT_DB_POOL_SIZE = 10
DEFAULT_DB_MAX_OVERFLOW = 20
DEFAULT_DB_POOL_TIMEOUT = 30
DEFAULT_DB_POOL_RECYCLE = 3600

# Cache
DEFAULT_CACHE_TTL = 3600  # 1 hour
MAX_CACHE_TTL = 604800  # 1 week
DEFAULT_CACHE_MAX_CONNECTIONS = 20

# =============================================================================
# API CONSTANTS
# =============================================================================

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_CONFLICT = 409
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503

# API Response Codes
SUCCESS_CODE = "success"
ERROR_CODE = "error"
VALIDATION_ERROR_CODE = "validation_error"
AUTHENTICATION_ERROR_CODE = "authentication_error"
AUTHORIZATION_ERROR_CODE = "authorization_error"
RATE_LIMIT_ERROR_CODE = "rate_limit_error"
INTERNAL_ERROR_CODE = "internal_error"

# =============================================================================
# TOOL EXECUTION CONSTANTS
# =============================================================================

# Timeouts
DEFAULT_TOOL_TIMEOUT = 30  # seconds
DEFAULT_TOOL_RETRY_ATTEMPTS = 3
DEFAULT_TOOL_RETRY_DELAY = 1.0  # seconds

# Circuit Breaker
DEFAULT_CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
DEFAULT_CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60  # seconds
DEFAULT_CIRCUIT_BREAKER_SUCCESS_THRESHOLD = 2

# =============================================================================
# VECTOR SEARCH CONSTANTS
# =============================================================================

# Vector Dimensions
DEFAULT_VECTOR_DIMENSION = 1536
MAX_VECTOR_DIMENSION = 4096

# Search Parameters
DEFAULT_SIMILARITY_THRESHOLD = 0.7
DEFAULT_MAX_SEARCH_RESULTS = 10
MAX_SEARCH_RESULTS = 100

# =============================================================================
# MONITORING CONSTANTS
# =============================================================================

# Metrics
DEFAULT_METRICS_PORT = 9090
METRICS_UPDATE_INTERVAL = 60  # seconds

# Health Check
HEALTH_CHECK_INTERVAL = 30  # seconds
HEALTH_CHECK_TIMEOUT = 10  # seconds
HEALTH_CHECK_RETRIES = 3

# Logging
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "json"
MAX_LOG_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_LOG_BACKUP_COUNT = 5

# =============================================================================
# FILE AND PATH CONSTANTS
# =============================================================================

# File Extensions
ALLOWED_FILE_EXTENSIONS = [".py", ".json", ".yaml", ".yml", ".txt", ".md"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Paths
DEFAULT_LOG_DIR = "/app/logs"
DEFAULT_DATA_DIR = "/app/data"
DEFAULT_POLICIES_DIR = "/app/policies"
DEFAULT_CACHE_DIR = "/app/cache"

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# String Lengths
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128
MIN_EMAIL_LENGTH = 5
MAX_EMAIL_LENGTH = 254
MIN_NAME_LENGTH = 1
MAX_NAME_LENGTH = 100
MIN_DESCRIPTION_LENGTH = 1
MAX_DESCRIPTION_LENGTH = 1000

# Regex Patterns
USERNAME_PATTERN = r"^[a-zA-Z0-9_-]+$"
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
URL_PATTERN = r"^https?://[^\s/$.?#].[^\s]*$"

# =============================================================================
# ENVIRONMENT CONSTANTS
# =============================================================================

# Environments
ENVIRONMENT_DEVELOPMENT = "development"
ENVIRONMENT_STAGING = "staging"
ENVIRONMENT_PRODUCTION = "production"

# Debug Settings
DEBUG_ENABLED = True
DEBUG_DISABLED = False

# =============================================================================
# ERROR MESSAGES
# =============================================================================

# Authentication
AUTH_INVALID_CREDENTIALS = "Invalid username or password"
AUTH_TOKEN_EXPIRED = "Token has expired"
AUTH_TOKEN_INVALID = "Invalid token"
AUTH_INSUFFICIENT_PERMISSIONS = "Insufficient permissions"
AUTH_ACCOUNT_LOCKED = "Account is locked"

# Validation
VALIDATION_REQUIRED_FIELD = "This field is required"
VALIDATION_INVALID_FORMAT = "Invalid format"
VALIDATION_TOO_SHORT = "Value is too short"
VALIDATION_TOO_LONG = "Value is too long"
VALIDATION_INVALID_CHARACTERS = "Invalid characters"

# Rate Limiting
RATE_LIMIT_EXCEEDED = "Rate limit exceeded"
RATE_LIMIT_RETRY_AFTER = "Retry after {seconds} seconds"

# Internal Errors
INTERNAL_ERROR_MESSAGE = "An internal server error occurred"
SERVICE_UNAVAILABLE_MESSAGE = "Service temporarily unavailable"

# =============================================================================
# CACHE KEYS
# =============================================================================

# Cache Key Prefixes
CACHE_PREFIX_USER = "user:"
CACHE_PREFIX_SESSION = "session:"
CACHE_PREFIX_TOOL = "tool:"
CACHE_PREFIX_POLICY = "policy:"
CACHE_PREFIX_RATE_LIMIT = "rate_limit:"
CACHE_PREFIX_HEALTH = "health:"

# Cache TTL Values
CACHE_TTL_USER = 3600  # 1 hour
CACHE_TTL_SESSION = 1800  # 30 minutes
CACHE_TTL_TOOL = 300  # 5 minutes
CACHE_TTL_POLICY = 600  # 10 minutes
CACHE_TTL_RATE_LIMIT = 60  # 1 minute
CACHE_TTL_HEALTH = 30  # 30 seconds
