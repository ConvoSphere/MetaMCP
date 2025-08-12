"""
API Module

This module provides the API layer for the MetaMCP application
with comprehensive versioning support.
"""

from .versioning import APIVersionManager, get_api_version_manager
from .router import create_api_router

__all__ = ["APIVersionManager", "get_api_version_manager", "create_api_router"]
