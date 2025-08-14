#!/usr/bin/env python3
"""
Environment Configuration Validator

This script validates the environment configuration for security and best practices.
"""

import os
import secrets
import sys
from typing import Any


def validate_environment() -> dict[str, Any]:
    """
    Validate environment configuration for security and best practices.

    Returns:
        Dict containing validation results
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "recommendations": [],
        "environment_info": {},
    }

    # Critical security variables
    critical_vars = {
        "SECRET_KEY": {
            "required": True,
            "min_length": 32,
            "description": "JWT secret key for token signing",
        },
        "DATABASE_URL": {"required": True, "description": "Database connection URL"},
        "OPENAI_API_KEY": {
            "required": False,
            "description": "OpenAI API key for LLM functionality",
        },
    }

    # Check critical variables
    for var, config in critical_vars.items():
        value = os.getenv(var)
        results["environment_info"][var] = (
            "***HIDDEN***" if "KEY" in var or "SECRET" in var else value
        )

        if config["required"] and not value:
            results["errors"].append(f"Required environment variable {var} is not set")
            results["valid"] = False
        elif value and "min_length" in config and len(value) < config["min_length"]:
            results["errors"].append(
                f"{var} must be at least {config['min_length']} characters long"
            )
            results["valid"] = False

    # Security validations
    validate_security_config(results)

    # Performance validations
    validate_performance_config(results)

    # Database validations
    validate_database_config(results)

    # Generate recommendations
    generate_recommendations(results)

    return results


def validate_security_config(results: dict[str, Any]) -> None:
    """Validate security-related configuration."""

    # Check for weak secret key
    secret_key = os.getenv("SECRET_KEY")
    if secret_key and secret_key == "your-secret-key-change-in-production":
        results["errors"].append("Must change default secret key in production")
        results["valid"] = False
    elif secret_key and len(secret_key) < 32:
        results["warnings"].append("Secret key should be at least 32 characters long")

    # Check for default admin credentials
    default_admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
    if (
        default_admin_password
        and default_admin_password == "your_secure_admin_password_here"
    ):
        results["warnings"].append("Change default admin password before deployment")

    # Check CORS configuration
    cors_origins = os.getenv("CORS_ORIGINS", "[]")
    if cors_origins == '["*"]':
        results["warnings"].append(
            "CORS is set to allow all origins - restrict in production"
        )

    # Check debug mode
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    if debug_mode:
        results["warnings"].append("Debug mode is enabled - disable in production")

    # Check environment
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        if debug_mode:
            results["errors"].append("Debug mode should not be enabled in production")
            results["valid"] = False

        if cors_origins == '["*"]':
            results["errors"].append("CORS should not allow all origins in production")
            results["valid"] = False


def validate_performance_config(results: dict[str, Any]) -> None:
    """Validate performance-related configuration."""

    # Check database pool settings
    try:
        pool_size = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        if pool_size < 5:
            results["warnings"].append(
                "Database pool size is very small - consider increasing"
            )
        elif pool_size > 50:
            results["warnings"].append(
                "Database pool size is very large - monitor performance"
            )
    except ValueError:
        results["errors"].append("DATABASE_POOL_SIZE must be a valid integer")
        results["valid"] = False

    # Check worker settings
    try:
        workers = int(os.getenv("WORKERS", "1"))
        if workers < 1:
            results["errors"].append("WORKERS must be at least 1")
            results["valid"] = False
        elif workers == 1:
            results["warnings"].append(
                "Single worker mode - consider multiple workers for production"
            )
    except ValueError:
        results["errors"].append("WORKERS must be a valid integer")
        results["valid"] = False


def validate_database_config(results: dict[str, Any]) -> None:
    """Validate database configuration."""

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Check for SQLite in production
        if (
            "sqlite" in database_url.lower()
            and os.getenv("ENVIRONMENT") == "production"
        ):
            results["warnings"].append("SQLite is not recommended for production use")

        # Check for weak passwords in URL
        if (
            "password" in database_url.lower()
            and "your_secure_password" in database_url
        ):
            results["warnings"].append("Change default database password")


def generate_recommendations(results: dict[str, Any]) -> None:
    """Generate security and performance recommendations."""

    recommendations = [
        "Use environment-specific .env files (.env.production, .env.staging)",
        "Enable HTTPS in production with proper SSL certificates",
        "Configure proper logging with log rotation",
        "Set up monitoring and alerting",
        "Use Redis for rate limiting and caching in production",
        "Configure backup strategies for databases",
        "Set up proper firewall rules",
        "Use secrets management for sensitive data",
        "Enable audit logging for security events",
        "Configure proper CORS origins for production",
    ]

    # Add specific recommendations based on current config
    if os.getenv("ENVIRONMENT") == "production":
        recommendations.extend(
            [
                "Disable debug mode and API documentation in production",
                "Use strong, unique passwords for all services",
                "Configure proper SSL/TLS certificates",
                "Set up intrusion detection and monitoring",
                "Implement proper backup and disaster recovery procedures",
            ]
        )

    results["recommendations"] = recommendations


def generate_secure_secret_key() -> str:
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)


def print_validation_results(results: dict[str, Any]) -> None:
    """Print validation results in a formatted way."""

    print("=" * 60)
    print("ENVIRONMENT CONFIGURATION VALIDATION")
    print("=" * 60)

    # Print validation status
    status = "✅ VALID" if results["valid"] else "❌ INVALID"
    print(f"Status: {status}")
    print()

    # Print errors
    if results["errors"]:
        print("❌ ERRORS:")
        for error in results["errors"]:
            print(f"   • {error}")
        print()

    # Print warnings
    if results["warnings"]:
        print("⚠️  WARNINGS:")
        for warning in results["warnings"]:
            print(f"   • {warning}")
        print()

    # Print environment info
    print("📋 ENVIRONMENT VARIABLES:")
    for var, value in results["environment_info"].items():
        print(f"   {var}: {value}")
    print()

    # Print recommendations
    if results["recommendations"]:
        print("💡 RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            print(f"   • {rec}")
        print()


def print_setup_instructions() -> None:
    """Print setup instructions for missing configuration."""

    print("🔧 SETUP INSTRUCTIONS:")
    print()

    print("1. Generate a secure secret key:")
    print(f"   export SECRET_KEY={generate_secure_secret_key()}")
    print()

    print("2. Set up database connection:")
    print("   export DATABASE_URL=postgresql://user:password@localhost/metamcp")
    print()

    print("3. Configure OpenAI API key (optional):")
    print("   export OPENAI_API_KEY=your_openai_api_key_here")
    print()

    print("4. For production deployment:")
    print("   export ENVIRONMENT=production")
    print("   export DEBUG=false")
    print("   export CORS_ORIGINS='[\"https://yourdomain.com\"]'")
    print()


def main() -> None:
    """Main function."""

    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        print_setup_instructions()
        return

    # Validate environment
    results = validate_environment()

    # Print results
    print_validation_results(results)

    # Exit with appropriate code
    if not results["valid"]:
        print("❌ Environment configuration is invalid. Please fix the errors above.")
        sys.exit(1)
    else:
        print("✅ Environment configuration is valid!")
        if results["warnings"]:
            print("⚠️  Please review the warnings and recommendations above.")
        sys.exit(0)


if __name__ == "__main__":
    main()
