#!/usr/bin/env python3
"""
Environment Variables Validation Script

This script validates the environment configuration for MetaMCP.
It checks for required variables, validates types, and provides helpful feedback.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def validate_environment() -> Dict[str, Any]:
    """
    Validate the current environment configuration.
    
    Returns:
        Dict containing validation results
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "missing_required": [],
        "environment_info": {}
    }
    
    try:
        # Get environment variables
        env_vars = {
            "APP_NAME": os.getenv("APP_NAME", "MetaMCP"),
            "APP_VERSION": os.getenv("APP_VERSION", "1.0.0"),
            "DEBUG": os.getenv("DEBUG", "false").lower() == "true",
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
            "HOST": os.getenv("HOST", "0.0.0.0"),
            "PORT": int(os.getenv("PORT", "8000")),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "SECRET_KEY": os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
            "DATABASE_URL": os.getenv("DATABASE_URL"),
            "WEAVIATE_URL": os.getenv("WEAVIATE_URL"),
            "REDIS_URL": os.getenv("REDIS_URL"),
            "OPA_URL": os.getenv("OPA_URL"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "VECTOR_SEARCH_ENABLED": os.getenv("VECTOR_SEARCH_ENABLED", "true").lower() == "true",
            "TELEMETRY_ENABLED": os.getenv("TELEMETRY_ENABLED", "true").lower() == "true",
            "OTLP_ENDPOINT": os.getenv("OTLP_ENDPOINT"),
            "ADMIN_ENABLED": os.getenv("ADMIN_ENABLED", "true").lower() == "true",
            "ADMIN_PORT": int(os.getenv("ADMIN_PORT", "8501")),
        }
        
        # Environment information
        results["environment_info"] = {
            "environment": env_vars["ENVIRONMENT"],
            "debug": env_vars["DEBUG"],
            "host": env_vars["HOST"],
            "port": env_vars["PORT"],
            "log_level": env_vars["LOG_LEVEL"]
        }
        
        # Check for missing required variables
        required_vars = [
            "SECRET_KEY",
            "DATABASE_URL",
            "WEAVIATE_URL",
            "REDIS_URL",
            "OPA_URL"
        ]
        
        for var in required_vars:
            if not env_vars.get(var):
                results["missing_required"].append(var)
                results["valid"] = False
        
        # Check for development-specific warnings
        if env_vars["ENVIRONMENT"] == "development":
            if env_vars["DEBUG"]:
                results["warnings"].append("Debug mode is enabled")
            
            if env_vars["SECRET_KEY"] == "your-secret-key-change-in-production":
                results["warnings"].append("Using default secret key - change for production")
        
        # Check for production-specific requirements
        if env_vars["ENVIRONMENT"] == "production":
            if env_vars["DEBUG"]:
                results["errors"].append("Debug mode should be disabled in production")
                results["valid"] = False
            
            if env_vars["SECRET_KEY"] == "your-secret-key-change-in-production":
                results["errors"].append("Must change default secret key in production")
                results["valid"] = False
            
            if not env_vars["OPENAI_API_KEY"]:
                results["warnings"].append("OpenAI API key not set")
        
        # Check vector search configuration
        if env_vars["VECTOR_SEARCH_ENABLED"]:
            if not env_vars["WEAVIATE_URL"]:
                results["errors"].append("Weaviate URL required when vector search is enabled")
                results["valid"] = False
        
        # Check telemetry configuration
        if env_vars["TELEMETRY_ENABLED"] and not env_vars["OTLP_ENDPOINT"]:
            results["warnings"].append("Telemetry enabled but OTLP endpoint not configured")
        
        # Check admin interface
        if env_vars["ADMIN_ENABLED"]:
            results["environment_info"]["admin_port"] = env_vars["ADMIN_PORT"]
        
    except Exception as e:
        results["valid"] = False
        results["errors"].append(f"Configuration error: {str(e)}")
    
    return results


def print_validation_results(results: Dict[str, Any]) -> None:
    """
    Print validation results in a formatted way.
    
    Args:
        results: Validation results dictionary
    """
    print("=" * 60)
    print("MetaMCP Environment Validation")
    print("=" * 60)
    
    # Environment information
    if results["environment_info"]:
        print("\n📋 Environment Information:")
        for key, value in results["environment_info"].items():
            print(f"   {key}: {value}")
    
    # Errors
    if results["errors"]:
        print("\n❌ Errors:")
        for error in results["errors"]:
            print(f"   • {error}")
    
    # Warnings
    if results["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in results["warnings"]:
            print(f"   • {warning}")
    
    # Missing required variables
    if results["missing_required"]:
        print("\n🔍 Missing Required Variables:")
        for var in results["missing_required"]:
            print(f"   • {var}")
    
    # Overall result
    print("\n" + "=" * 60)
    if results["valid"]:
        print("✅ Environment configuration is valid!")
    else:
        print("❌ Environment configuration has issues!")
    print("=" * 60)


def suggest_fixes(results: Dict[str, Any]) -> None:
    """
    Suggest fixes for validation issues.
    
    Args:
        results: Validation results dictionary
    """
    if not results["errors"] and not results["missing_required"]:
        return
    
    print("\n🔧 Suggested Fixes:")
    
    # Fix missing required variables
    if results["missing_required"]:
        print("\n   Set these environment variables:")
        for var in results["missing_required"]:
            if var == "SECRET_KEY":
                print(f"   export {var}=$(openssl rand -hex 32)")
            elif var == "DATABASE_URL":
                print(f"   export {var}=postgresql://user:password@localhost/metamcp")
            elif var == "WEAVIATE_URL":
                print(f"   export {var}=http://localhost:8080")
            elif var == "REDIS_URL":
                print(f"   export {var}=redis://localhost:6379")
            elif var == "OPA_URL":
                print(f"   export {var}=http://localhost:8181")
    
    # Fix errors
    if results["errors"]:
        print("\n   Fix these issues:")
        for error in results["errors"]:
            if "Debug mode should be disabled" in error:
                print("   • Set DEBUG=false for production")
            elif "Must change default secret key" in error:
                print("   • Generate a new SECRET_KEY for production")
            elif "Weaviate URL required" in error:
                print("   • Set WEAVIATE_URL or disable VECTOR_SEARCH_ENABLED")


def main() -> int:
    """
    Main function to run environment validation.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        results = validate_environment()
        print_validation_results(results)
        
        if results["errors"] or results["missing_required"]:
            suggest_fixes(results)
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 