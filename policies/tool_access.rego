# =============================================================================
# MCP Meta-Server Tool Access Policy
# =============================================================================
#
# This policy defines access control rules for tool operations in the
# MCP Meta-Server. It implements role-based access control (RBAC) with
# support for different security levels and user roles.

package metamcp.tools

import future.keywords.if
import future.keywords.in

# Default policy: deny access unless explicitly allowed
default allow := false

# =============================================================================
# Main Authorization Logic
# =============================================================================

# Allow access if user has admin role
allow if {
    input.user.role == "admin"
}

# Allow tool execution for authenticated agents
allow if {
    input.user.role == "agent"
    input.action == "execute"
    tool_access_permitted
}

# Allow tool reading for authenticated users
allow if {
    input.user.role in ["agent", "user", "developer"]
    input.action == "read"
    tool_access_permitted
}

# Allow tool registration for developers and admins
allow if {
    input.user.role in ["developer", "admin"]
    input.action in ["create", "update", "delete"]
    input.resource == "registry"
}

# Allow tool updates for tool owners
allow if {
    input.user.role == "developer"
    input.action in ["update", "delete"]
    tool_owner_check
}

# =============================================================================
# Helper Rules
# =============================================================================

# Check if tool access is permitted based on security level
tool_access_permitted if {
    input.tool.security_level <= input.user.clearance_level
}

# Check if user is the owner of the tool
tool_owner_check if {
    input.tool.author == input.user.username
}

# Check if tool is in allowed categories for user
tool_category_allowed if {
    input.tool.category in input.user.allowed_categories
}

# Check if user has specific permission for the tool
user_has_permission if {
    permission := sprintf("tools:%s:%s", [input.action, input.resource])
    permission in input.user.permissions
}

# =============================================================================
# Security Level Rules
# =============================================================================

# Public tools (security level 0) - accessible to all authenticated users
tool_access_permitted if {
    input.tool.security_level == 0
    input.user.authenticated == true
}

# Restricted tools (security level 1-3) - require appropriate clearance
tool_access_permitted if {
    input.tool.security_level > 0
    input.tool.security_level <= 3
    input.user.clearance_level >= input.tool.security_level
}

# Confidential tools (security level 4-6) - require special authorization
tool_access_permitted if {
    input.tool.security_level > 3
    input.tool.security_level <= 6
    input.user.clearance_level >= input.tool.security_level
    tool_category_allowed
}

# Secret tools (security level 7-10) - require admin approval
tool_access_permitted if {
    input.tool.security_level > 6
    input.user.role == "admin"
}

# =============================================================================
# Time-based Access Rules
# =============================================================================

# Check if access is within allowed time window
time_window_allowed if {
    not input.user.time_restrictions
}

time_window_allowed if {
    input.user.time_restrictions
    current_hour := time.now_ns() / 1000000000 / 3600 % 24
    current_hour >= input.user.allowed_hours.start
    current_hour <= input.user.allowed_hours.end
}

# =============================================================================
# Rate Limiting Rules
# =============================================================================

# Check if user hasn't exceeded rate limits
rate_limit_ok if {
    not input.user.rate_limit
}

rate_limit_ok if {
    input.user.rate_limit
    input.user.current_requests < input.user.rate_limit.max_requests
}

# =============================================================================
# Audit Logging
# =============================================================================

# Generate audit log entry for policy evaluation
audit_entry := {
    "timestamp": time.now_ns(),
    "user_id": input.user.id,
    "action": input.action,
    "resource": input.resource,
    "tool_name": input.tool.name,
    "security_level": input.tool.security_level,
    "decision": allow,
    "policy": "tool_access"
}

# =============================================================================
# Policy Violations
# =============================================================================

# Define specific violation reasons
violation_reason := "insufficient_clearance" if {
    not allow
    input.tool.security_level > input.user.clearance_level
}

violation_reason := "role_not_authorized" if {
    not allow
    not input.user.role in ["admin", "agent", "user", "developer"]
}

violation_reason := "time_restriction" if {
    not allow
    not time_window_allowed
}

violation_reason := "rate_limit_exceeded" if {
    not allow
    not rate_limit_ok
}

violation_reason := "category_not_allowed" if {
    not allow
    input.tool.category
    not tool_category_allowed
}

violation_reason := "general_denial" if {
    not allow
    not violation_reason
}