"""
Admin UI Development

This module provides a web-based admin interface with user management,
system monitoring, and tool management dashboards.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from ..config import get_settings
from ..utils.logging import get_logger
from ..utils.error_handler import get_error_stats
from ..utils.rate_limiter import create_rate_limiter
from ..utils.api_versioning import get_supported_versions

logger = get_logger(__name__)


@dataclass
class SystemMetrics:
    """System metrics for admin dashboard."""
    uptime_seconds: int
    total_requests: int
    error_count: int
    active_connections: int
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_usage_percent: float
    timestamp: datetime


@dataclass
class UserInfo:
    """User information for admin dashboard."""
    user_id: str
    username: str
    email: str
    role: str
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    api_keys: List[str]


@dataclass
class ToolInfo:
    """Tool information for admin dashboard."""
    tool_id: str
    name: str
    description: str
    version: str
    status: str
    last_used: Optional[datetime]
    usage_count: int
    error_count: int


class AdminDashboard:
    """Main admin dashboard class."""
    
    def __init__(self):
        """Initialize admin dashboard."""
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        self.start_time = datetime.utcnow()
        
        # Initialize components
        self.rate_limiter = create_rate_limiter(use_redis=False)
        
    def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview metrics."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Get error statistics
        error_stats = get_error_stats()
        
        return {
            "system": {
                "uptime_seconds": int(uptime),
                "uptime_formatted": self._format_uptime(uptime),
                "version": self.settings.app_version,
                "environment": self.settings.environment,
                "start_time": self.start_time.isoformat()
            },
            "metrics": {
                "total_requests": error_stats.get("total_errors", 0) + 1000,  # Mock data
                "error_count": error_stats.get("total_errors", 0),
                "active_connections": 25,  # Mock data
                "memory_usage_mb": 128.5,  # Mock data
                "cpu_usage_percent": 15.2,  # Mock data
                "disk_usage_percent": 45.8  # Mock data
            },
            "errors": {
                "by_severity": error_stats.get("by_severity", {}),
                "by_category": error_stats.get("by_category", {}),
                "recent_errors": error_stats.get("recent_errors", [])
            }
        }
    
    def get_user_management_data(self) -> Dict[str, Any]:
        """Get user management data."""
        # Mock user data - in real implementation, this would come from database
        users = [
            UserInfo(
                user_id="user-1",
                username="admin",
                email="admin@example.com",
                role="admin",
                created_at=datetime.utcnow() - timedelta(days=30),
                last_login=datetime.utcnow() - timedelta(hours=2),
                is_active=True,
                api_keys=["admin-key-1", "admin-key-2"]
            ),
            UserInfo(
                user_id="user-2",
                username="user1",
                email="user1@example.com",
                role="user",
                created_at=datetime.utcnow() - timedelta(days=15),
                last_login=datetime.utcnow() - timedelta(days=1),
                is_active=True,
                api_keys=["test-key-1"]
            ),
            UserInfo(
                user_id="user-3",
                username="user2",
                email="user2@example.com",
                role="user",
                created_at=datetime.utcnow() - timedelta(days=7),
                last_login=None,
                is_active=False,
                api_keys=[]
            )
        ]
        
        return {
            "users": [asdict(user) for user in users],
            "statistics": {
                "total_users": len(users),
                "active_users": len([u for u in users if u.is_active]),
                "admin_users": len([u for u in users if u.role == "admin"]),
                "users_with_api_keys": len([u for u in users if u.api_keys])
            }
        }
    
    def get_tool_management_data(self) -> Dict[str, Any]:
        """Get tool management data."""
        # Mock tool data - in real implementation, this would come from tool registry
        tools = [
            ToolInfo(
                tool_id="tool-1",
                name="Search Tool",
                description="Semantic search functionality",
                version="1.0.0",
                status="active",
                last_used=datetime.utcnow() - timedelta(minutes=30),
                usage_count=1250,
                error_count=5
            ),
            ToolInfo(
                tool_id="tool-2",
                name="Translation Tool",
                description="Language translation service",
                version="1.2.0",
                status="active",
                last_used=datetime.utcnow() - timedelta(hours=2),
                usage_count=890,
                error_count=12
            ),
            ToolInfo(
                tool_id="tool-3",
                name="Image Generator",
                description="AI image generation",
                version="0.9.5",
                status="maintenance",
                last_used=datetime.utcnow() - timedelta(days=1),
                usage_count=450,
                error_count=25
            )
        ]
        
        return {
            "tools": [asdict(tool) for tool in tools],
            "statistics": {
                "total_tools": len(tools),
                "active_tools": len([t for t in tools if t.status == "active"]),
                "total_usage": sum(t.usage_count for t in tools),
                "total_errors": sum(t.error_count for t in tools)
            }
        }
    
    def get_api_management_data(self) -> Dict[str, Any]:
        """Get API management data."""
        supported_versions = get_supported_versions()
        
        return {
            "versions": {
                "supported_versions": supported_versions,
                "current_version": "v1",
                "latest_version": supported_versions[-1] if supported_versions else "v1"
            },
            "rate_limiting": {
                "enabled": True,
                "default_limit": self.settings.rate_limit_requests,
                "default_window": self.settings.rate_limit_window
            },
            "security": {
                "request_signing": self.settings.environment == "production",
                "api_keys_enabled": True,
                "ip_whitelist_enabled": False
            }
        }
    
    def get_monitoring_data(self) -> Dict[str, Any]:
        """Get monitoring and alerting data."""
        return {
            "alerts": [
                {
                    "id": "alert-1",
                    "severity": "warning",
                    "message": "High error rate detected",
                    "timestamp": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                    "resolved": False
                },
                {
                    "id": "alert-2",
                    "severity": "info",
                    "message": "New API version available",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "resolved": True
                }
            ],
            "logs": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "INFO",
                    "message": "Request processed successfully",
                    "user_id": "user-1"
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                    "level": "WARNING",
                    "message": "Rate limit exceeded",
                    "user_id": "user-2"
                }
            ]
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


class AdminAPI:
    """Admin API endpoints."""
    
    def __init__(self):
        """Initialize admin API."""
        self.dashboard = AdminDashboard()
        self.logger = get_logger(__name__)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data."""
        return {
            "system": self.dashboard.get_system_overview(),
            "users": self.dashboard.get_user_management_data(),
            "tools": self.dashboard.get_tool_management_data(),
            "api": self.dashboard.get_api_management_data(),
            "monitoring": self.dashboard.get_monitoring_data()
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        return self.dashboard.get_system_overview()
    
    def get_user_list(self) -> Dict[str, Any]:
        """Get user list."""
        return self.dashboard.get_user_management_data()
    
    def get_tool_list(self) -> Dict[str, Any]:
        """Get tool list."""
        return self.dashboard.get_tool_management_data()
    
    def get_api_info(self) -> Dict[str, Any]:
        """Get API information."""
        return self.dashboard.get_api_management_data()
    
    def get_monitoring_info(self) -> Dict[str, Any]:
        """Get monitoring information."""
        return self.dashboard.get_monitoring_data()


# Global admin API instance
admin_api = AdminAPI()


def get_admin_dashboard_data() -> Dict[str, Any]:
    """Get admin dashboard data."""
    return admin_api.get_dashboard_data()


def get_system_metrics() -> Dict[str, Any]:
    """Get system metrics."""
    return admin_api.get_system_metrics()


def get_user_management_data() -> Dict[str, Any]:
    """Get user management data."""
    return admin_api.get_user_list()


def get_tool_management_data() -> Dict[str, Any]:
    """Get tool management data."""
    return admin_api.get_tool_list() 