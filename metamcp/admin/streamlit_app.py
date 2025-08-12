"""
Streamlit Admin Interface

This module provides a Streamlit-based admin interface that communicates
exclusively through the Admin API to maintain clean separation.
"""

import json
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# Configuration
import os

API_BASE_URL = os.getenv("ADMIN_API_URL", "http://localhost:8000/api/v1/admin/")
AUTO_REFRESH_INTERVAL = int(
    os.getenv("ADMIN_AUTO_REFRESH_INTERVAL", "30000")
)  # 30 seconds

# Page configuration
st.set_page_config(
    page_title="MetaMCP Admin",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-active {
        color: #28a745;
        font-weight: bold;
    }
    .status-inactive {
        color: #dc3545;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)


def make_api_request(
    endpoint: str, method: str = "GET", data: Optional[Dict] = None
) -> Dict[str, Any]:
    """Make API request to admin endpoints."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}

        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {}


def get_dashboard_data() -> Dict[str, Any]:
    """Get dashboard data from API."""
    return make_api_request("dashboard")


def get_system_metrics() -> Dict[str, Any]:
    """Get system metrics from API."""
    return make_api_request("system/metrics")


def get_users(
    page: int = 1,
    limit: int = 50,
    search: str = "",
    role: str = "",
    is_active: Optional[bool] = None,
) -> Dict[str, Any]:
    """Get users from API with filtering and pagination."""
    params = f"page={page}&limit={limit}"
    if search:
        params += f"&search={search}"
    if role:
        params += f"&role={role}"
    if is_active is not None:
        params += f"&is_active={is_active}"

    return make_api_request(f"users?{params}")


def get_tools(
    page: int = 1,
    limit: int = 50,
    search: str = "",
    status: str = "",
    is_active: Optional[bool] = None,
) -> Dict[str, Any]:
    """Get tools from API with filtering and pagination."""
    params = f"page={page}&limit={limit}"
    if search:
        params += f"&search={search}"
    if status:
        params += f"&status={status}"
    if is_active is not None:
        params += f"&is_active={is_active}"

    return make_api_request(f"tools?{params}")


def get_logs(level: str = "", limit: int = 100) -> Dict[str, Any]:
    """Get system logs from API."""
    params = f"limit={limit}"
    if level:
        params += f"&level={level}"

    return make_api_request(f"logs?{params}")


def create_user(user_data: Dict[str, Any]) -> bool:
    """Create a new user via API."""
    response = make_api_request("users", method="POST", data=user_data)
    return "user_id" in response


def update_user(user_id: str, user_data: Dict[str, Any]) -> bool:
    """Update a user via API."""
    response = make_api_request(f"users/{user_id}", method="PUT", data=user_data)
    return "message" in response


def delete_user(user_id: str) -> bool:
    """Delete a user via API."""
    response = make_api_request(f"users/{user_id}", method="DELETE")
    return "message" in response


def create_tool(tool_data: Dict[str, Any]) -> bool:
    """Create a new tool via API."""
    response = make_api_request("tools", method="POST", data=tool_data)
    return "tool_id" in response


def update_tool(tool_id: str, tool_data: Dict[str, Any]) -> bool:
    """Update a tool via API."""
    response = make_api_request(f"tools/{tool_id}", method="PUT", data=tool_data)
    return "message" in response


def delete_tool(tool_id: str) -> bool:
    """Delete a tool via API."""
    response = make_api_request(f"tools/{tool_id}", method="DELETE")
    return "message" in response


def restart_system() -> bool:
    """Restart the system via API."""
    response = make_api_request("system/restart", method="POST")
    return "message" in response


def main():
    """Main Streamlit application."""

    # Auto-refresh
    st_autorefresh(interval=AUTO_REFRESH_INTERVAL, key="admin_refresh")

    # Sidebar navigation
    st.sidebar.title("🔧 MetaMCP Admin")
    page = st.sidebar.selectbox(
        "Navigation",
        [
            "Dashboard",
            "User Management",
            "Tool Management",
            "System Monitoring",
            "Logs",
            "System Control",
        ],
    )

    # Main content
    if page == "Dashboard":
        show_dashboard()
    elif page == "User Management":
        show_user_management()
    elif page == "Tool Management":
        show_tool_management()
    elif page == "System Monitoring":
        show_system_monitoring()
    elif page == "Logs":
        show_logs()
    elif page == "System Control":
        show_system_control()


def show_dashboard():
    """Show main dashboard."""
    st.markdown(
        '<h1 class="main-header">MetaMCP Admin Dashboard</h1>', unsafe_allow_html=True
    )

    # Get dashboard data
    dashboard_data = get_dashboard_data()

    if not dashboard_data:
        st.error("Failed to load dashboard data")
        return

    # System overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Uptime", dashboard_data.get("system", {}).get("uptime_formatted", "N/A")
        )

    with col2:
        st.metric(
            "Total Requests", dashboard_data.get("metrics", {}).get("total_requests", 0)
        )

    with col3:
        st.metric(
            "Error Rate", f"{dashboard_data.get('metrics', {}).get('error_count', 0)}"
        )

    with col4:
        st.metric(
            "Active Connections",
            dashboard_data.get("metrics", {}).get("active_connections", 0),
        )

    # System metrics charts
    col1, col2 = st.columns(2)

    with col1:
        # Memory usage
        memory_data = dashboard_data.get("metrics", {})
        fig_memory = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=memory_data.get("memory_usage_mb", 0),
                title={"text": "Memory Usage (MB)"},
                gauge={
                    "axis": {"range": [None, 1000]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 500], "color": "lightgray"},
                        {"range": [500, 800], "color": "yellow"},
                        {"range": [800, 1000], "color": "red"},
                    ],
                },
            )
        )
        st.plotly_chart(fig_memory, use_container_width=True)

    with col2:
        # CPU usage
        cpu_data = dashboard_data.get("metrics", {})
        fig_cpu = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=cpu_data.get("cpu_usage_percent", 0),
                title={"text": "CPU Usage (%)"},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "darkgreen"},
                    "steps": [
                        {"range": [0, 50], "color": "lightgray"},
                        {"range": [50, 80], "color": "yellow"},
                        {"range": [80, 100], "color": "red"},
                    ],
                },
            )
        )
        st.plotly_chart(fig_cpu, use_container_width=True)

    # Recent activity
    st.subheader("Recent Activity")
    if "recent_activity" in dashboard_data:
        activity_df = pd.DataFrame(dashboard_data["recent_activity"])
        st.dataframe(activity_df, use_container_width=True)
    else:
        st.info("No recent activity data available")


def show_user_management():
    """Show user management interface."""
    st.title("👥 User Management")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        search = st.text_input("Search users", "")

    with col2:
        role_filter = st.selectbox("Filter by role", ["", "admin", "user", "moderator"])

    with col3:
        status_filter = st.selectbox("Filter by status", ["", "Active", "Inactive"])

    with col4:
        page_size = st.selectbox("Page size", [10, 25, 50, 100])

    # Get users
    is_active_filter = None
    if status_filter == "Active":
        is_active_filter = True
    elif status_filter == "Inactive":
        is_active_filter = False

    users_data = get_users(
        page=1,
        limit=page_size,
        search=search,
        role=role_filter,
        is_active=is_active_filter,
    )

    if not users_data:
        st.error("Failed to load users")
        return

    # Create user button
    if st.button("➕ Create New User"):
        st.session_state.show_create_user = True

    # Create user form
    if st.session_state.get("show_create_user", False):
        with st.form("create_user_form"):
            st.subheader("Create New User")

            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username *")
                email = st.text_input("Email *")
                password = st.text_input("Password *", type="password")

            with col2:
                full_name = st.text_input("Full Name")
                roles = st.multiselect(
                    "Roles", ["user", "admin", "moderator"], default=["user"]
                )
                is_active = st.checkbox("Active", value=True)
                is_admin = st.checkbox("Admin", value=False)

            submitted = st.form_submit_button("Create User")
            if submitted:
                if username and email and password:
                    user_data = {
                        "username": username,
                        "email": email,
                        "password": password,
                        "full_name": full_name,
                        "roles": roles,
                        "is_active": is_active,
                        "is_admin": is_admin,
                    }

                    if create_user(user_data):
                        st.success("User created successfully!")
                        st.session_state.show_create_user = False
                        st.rerun()
                    else:
                        st.error("Failed to create user")
                else:
                    st.error("Please fill in all required fields")

    # Users table
    users = users_data.get("users", [])
    if users:
        # Convert to DataFrame for better display
        df_data = []
        for user in users:
            df_data.append(
                {
                    "ID": user.get("user_id", ""),
                    "Username": user.get("username", ""),
                    "Email": user.get("email", ""),
                    "Full Name": user.get("full_name", ""),
                    "Roles": ", ".join(user.get("roles", [])),
                    "Status": "🟢 Active" if user.get("is_active") else "🔴 Inactive",
                    "Created": user.get("created_at", ""),
                    "Last Login": user.get("last_login", "Never"),
                }
            )

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)

        # Pagination info
        pagination = users_data.get("pagination", {})
        if pagination:
            st.info(
                f"Showing page {pagination.get('page', 1)} of {pagination.get('pages', 1)} "
                f"({pagination.get('total', 0)} total users)"
            )
    else:
        st.info("No users found")


def show_tool_management():
    """Show tool management interface."""
    st.title("🛠️ Tool Management")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        search = st.text_input("Search tools", "")

    with col2:
        status_filter = st.selectbox(
            "Filter by status", ["", "active", "inactive", "error"]
        )

    with col3:
        active_filter = st.selectbox(
            "Filter by active status", ["", "Active", "Inactive"]
        )

    with col4:
        page_size = st.selectbox("Page size", [10, 25, 50, 100])

    # Get tools
    is_active_filter = None
    if active_filter == "Active":
        is_active_filter = True
    elif active_filter == "Inactive":
        is_active_filter = False

    tools_data = get_tools(
        page=1,
        limit=page_size,
        search=search,
        status=status_filter,
        is_active=is_active_filter,
    )

    if not tools_data:
        st.error("Failed to load tools")
        return

    # Create tool button
    if st.button("➕ Create New Tool"):
        st.session_state.show_create_tool = True

    # Create tool form
    if st.session_state.get("show_create_tool", False):
        with st.form("create_tool_form"):
            st.subheader("Create New Tool")

            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Tool Name *")
                description = st.text_area("Description *")
                version = st.text_input("Version", value="1.0.0")
                endpoint_url = st.text_input("Endpoint URL *")

            with col2:
                auth_type = st.selectbox(
                    "Authentication Type", ["none", "api_key", "oauth", "basic"]
                )
                is_active = st.checkbox("Active", value=True)
                schema_json = st.text_area("Schema (JSON)", value="{}")

            submitted = st.form_submit_button("Create Tool")
            if submitted:
                if name and description and endpoint_url:
                    try:
                        schema = json.loads(schema_json) if schema_json else {}
                        tool_data = {
                            "name": name,
                            "description": description,
                            "version": version,
                            "endpoint_url": endpoint_url,
                            "authentication_type": auth_type,
                            "schema": schema,
                            "is_active": is_active,
                        }

                        if create_tool(tool_data):
                            st.success("Tool created successfully!")
                            st.session_state.show_create_tool = False
                            st.rerun()
                        else:
                            st.error("Failed to create tool")
                    except json.JSONDecodeError:
                        st.error("Invalid JSON schema")
                else:
                    st.error("Please fill in all required fields")

    # Tools table
    tools = tools_data.get("tools", [])
    if tools:
        # Convert to DataFrame for better display
        df_data = []
        for tool in tools:
            status_emoji = (
                "🟢"
                if tool.get("status") == "active"
                else "🔴" if tool.get("status") == "inactive" else "🟡"
            )
            df_data.append(
                {
                    "ID": tool.get("tool_id", ""),
                    "Name": tool.get("name", ""),
                    "Description": (
                        tool.get("description", "")[:50] + "..."
                        if len(tool.get("description", "")) > 50
                        else tool.get("description", "")
                    ),
                    "Version": tool.get("version", ""),
                    "Status": f"{status_emoji} {tool.get('status', '').title()}",
                    "Usage Count": tool.get("usage_count", 0),
                    "Error Count": tool.get("error_count", 0),
                    "Last Used": tool.get("last_used", "Never"),
                }
            )

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)

        # Pagination info
        pagination = tools_data.get("pagination", {})
        if pagination:
            st.info(
                f"Showing page {pagination.get('page', 1)} of {pagination.get('pages', 1)} "
                f"({pagination.get('total', 0)} total tools)"
            )
    else:
        st.info("No tools found")


def show_system_monitoring():
    """Show system monitoring interface."""
    st.title("📊 System Monitoring")

    # Get system metrics
    metrics_data = get_system_metrics()

    if not metrics_data:
        st.error("Failed to load system metrics")
        return

    # Real-time metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Memory Usage", f"{metrics_data.get('memory_usage_mb', 0):.1f} MB")

    with col2:
        st.metric("CPU Usage", f"{metrics_data.get('cpu_usage_percent', 0):.1f}%")

    with col3:
        st.metric("Disk Usage", f"{metrics_data.get('disk_usage_percent', 0):.1f}%")

    with col4:
        st.metric("Active Connections", metrics_data.get("active_connections", 0))

    # System health indicators
    st.subheader("System Health")

    # Memory chart
    memory_usage = metrics_data.get("memory_usage_mb", 0)
    memory_threshold = 800  # MB

    col1, col2 = st.columns(2)

    with col1:
        fig_memory = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=memory_usage,
                title={"text": "Memory Usage"},
                delta={"reference": memory_threshold},
                gauge={
                    "axis": {"range": [None, 1000]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 500], "color": "lightgray"},
                        {"range": [500, 800], "color": "yellow"},
                        {"range": [800, 1000], "color": "red"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": memory_threshold,
                    },
                },
            )
        )
        st.plotly_chart(fig_memory, use_container_width=True)

    with col2:
        # CPU chart
        cpu_usage = metrics_data.get("cpu_usage_percent", 0)
        fig_cpu = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=cpu_usage,
                title={"text": "CPU Usage"},
                delta={"reference": 80},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "darkgreen"},
                    "steps": [
                        {"range": [0, 50], "color": "lightgray"},
                        {"range": [50, 80], "color": "yellow"},
                        {"range": [80, 100], "color": "red"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 80,
                    },
                },
            )
        )
        st.plotly_chart(fig_cpu, use_container_width=True)

    # System information
    st.subheader("System Information")

    system_info = metrics_data.get("system", {})
    if system_info:
        col1, col2 = st.columns(2)

        with col1:
            st.info(f"**Version:** {system_info.get('version', 'N/A')}")
            st.info(f"**Environment:** {system_info.get('environment', 'N/A')}")

        with col2:
            st.info(f"**Uptime:** {system_info.get('uptime_formatted', 'N/A')}")
            st.info(f"**Start Time:** {system_info.get('start_time', 'N/A')}")


def show_logs():
    """Show system logs interface."""
    st.title("📋 System Logs")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        log_level = st.selectbox(
            "Log Level", ["", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )

    with col2:
        log_limit = st.slider(
            "Number of logs", min_value=10, max_value=1000, value=100, step=10
        )

    with col3:
        if st.button("🔄 Refresh Logs"):
            st.rerun()

    # Get logs
    logs_data = get_logs(level=log_level, limit=log_limit)

    if not logs_data:
        st.error("Failed to load logs")
        return

    logs = logs_data.get("logs", [])

    if logs:
        # Convert to DataFrame for better display
        df_data = []
        for log in logs:
            level_emoji = {
                "DEBUG": "🔍",
                "INFO": "ℹ️",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "CRITICAL": "🚨",
            }.get(log.get("level", ""), "📝")

            df_data.append(
                {
                    "Timestamp": log.get("timestamp", ""),
                    "Level": f"{level_emoji} {log.get('level', '')}",
                    "Message": log.get("message", ""),
                    "Module": log.get("module", ""),
                }
            )

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)

        # Log statistics
        st.subheader("Log Statistics")

        if logs:
            level_counts = {}
            for log in logs:
                level = log.get("level", "UNKNOWN")
                level_counts[level] = level_counts.get(level, 0) + 1

            if level_counts:
                fig = px.pie(
                    values=list(level_counts.values()),
                    names=list(level_counts.keys()),
                    title="Log Distribution by Level",
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No logs found")


def show_system_control():
    """Show system control interface."""
    st.title("⚙️ System Control")

    st.warning("⚠️ These actions affect the entire system. Use with caution!")

    # System restart
    st.subheader("System Restart")
    st.info(
        "Restart the entire MetaMCP system. This will temporarily interrupt all services."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Restart System", type="primary"):
            if restart_system():
                st.success("System restart initiated successfully!")
            else:
                st.error("Failed to initiate system restart")

    with col2:
        st.info("**Note:** System restart may take 30-60 seconds to complete.")

    # Configuration
    st.subheader("System Configuration")

    config_data = make_api_request("config")

    if config_data:
        st.json(config_data)
    else:
        st.error("Failed to load system configuration")

    # Health check
    st.subheader("System Health")

    health_data = make_api_request("health")

    if health_data:
        status = health_data.get("status", "unknown")
        service = health_data.get("service", "unknown")

        if status == "healthy":
            st.success(f"✅ {service} is healthy")
        else:
            st.error(f"❌ {service} is not healthy")
    else:
        st.error("Failed to get system health status")


if __name__ == "__main__":
    # Initialize session state
    if "show_create_user" not in st.session_state:
        st.session_state.show_create_user = False
    if "show_create_tool" not in st.session_state:
        st.session_state.show_create_tool = False

    main()
