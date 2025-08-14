"""
API Module

This module provides the API layer for the MetaMCP application
with comprehensive versioning support.
"""

from .router import create_api_router
from .versioning import APIVersionManager, get_api_version_manager

__all__ = ["APIVersionManager", "get_api_version_manager", "create_api_router"]
