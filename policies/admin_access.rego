# =============================================================================
# MCP Meta-Server Admin Access Policy
# =============================================================================
#
# This policy defines access control rules for administrative operations
# in the MCP Meta-Server including system management, user management,
# and policy configuration.

package metamcp.admin

import future.keywords.if
import future.keywords.in

# Default policy: deny admin access unless explicitly allowed
default allow := false

# =============================================================================
# Main Authorization Logic
# =============================================================================

# Allow full admin access for super admin role
allow if {
    input.user.role == "super_admin"
}

# Allow specific admin operations for admin role
allow if {
    input.user.role == "admin"
    admin_operation_allowed
}

# Allow read-only admin operations for moderator role
allow if {
    input.user.role == "moderator"
    input.action == "read"
    moderator_resource_allowed
}

# =============================================================================
# Admin Operation Rules
# =============================================================================

# System management operations
admin_operation_allowed if {
    input.action in ["read", "update"]
    input.resource == "system_config"
}

# User management operations
admin_operation_allowed if {
    input.action in ["read", "create", "update", "delete"]
    input.resource == "users"
}

# Policy management operations
admin_operation_allowed if {
    input.action in ["read", "update"]
    input.resource == "policies"
}

# Audit log access
admin_operation_allowed if {
    input.action == "read"
    input.resource == "audit_logs"
}

# Metrics and monitoring access
admin_operation_allowed if {
    input.action == "read"
    input.resource in ["metrics", "health", "status"]
}

# Tool registry management
admin_operation_allowed if {
    input.action in ["read", "create", "update", "delete"]
    input.resource == "tool_registry"
}

# =============================================================================
# Moderator Resource Rules
# =============================================================================

# Resources that moderators can read
moderator_resource_allowed if {
    input.resource in [
        "users",
        "audit_logs", 
        "metrics",
        "health",
        "tool_registry"
    ]
}

# =============================================================================
# Sensitive Operations
# =============================================================================

# Operations that require super admin privileges
sensitive_operation if {
    input.resource == "system_config"
    input.action in ["create", "delete"]
}

sensitive_operation if {
    input.resource == "policies"
    input.action in ["create", "delete"]
}

sensitive_operation if {
    input.resource == "security_config"
}

# Block sensitive operations for non-super admins
allow if {
    sensitive_operation
    false  # Always deny
}

# =============================================================================
# Time-based Access Control
# =============================================================================

# Check business hours for admin operations
business_hours if {
    current_hour := time.now_ns() / 1000000000 / 3600 % 24
    current_hour >= 8
    current_hour <= 18
}

# Require business hours for sensitive operations
allow if {
    sensitive_operation
    input.user.role == "super_admin"
    business_hours
}

# =============================================================================
# Multi-factor Authentication
# =============================================================================

# Require MFA for admin operations
mfa_verified if {
    input.user.mfa_verified == true
}

# Block admin operations without MFA
allow if {
    input.user.role in ["admin", "super_admin"]
    not mfa_verified
    false  # Always deny
}

# =============================================================================
# IP Address Restrictions
# =============================================================================

# Check if request comes from allowed IP range
ip_allowed if {
    not input.user.ip_restrictions
}

ip_allowed if {
    input.user.ip_restrictions
    input.request.ip_address
    net.cidr_contains(input.user.allowed_ip_ranges[_], input.request.ip_address)
}

# =============================================================================
# Session Validation
# =============================================================================

# Check session validity
session_valid if {
    input.user.session_expires > time.now_ns()
}

session_valid if {
    not input.user.session_expires
}

# =============================================================================
# Audit Requirements
# =============================================================================

# Generate detailed audit entry for admin operations
admin_audit_entry := {
    "timestamp": time.now_ns(),
    "user_id": input.user.id,
    "username": input.user.username,
    "role": input.user.role,
    "action": input.action,
    "resource": input.resource,
    "ip_address": input.request.ip_address,
    "user_agent": input.request.user_agent,
    "mfa_verified": input.user.mfa_verified,
    "session_id": input.user.session_id,
    "decision": allow,
    "policy": "admin_access",
    "sensitive_operation": sensitive_operation
}

# =============================================================================
# Emergency Access
# =============================================================================

# Emergency break-glass access (must be explicitly enabled)
emergency_access if {
    input.emergency_mode == true
    input.user.role == "super_admin"
    input.emergency_code
    # Emergency code validation would be implemented in the application
}

# Allow emergency access with additional logging
allow if {
    emergency_access
    # Additional audit logging required for emergency access
}

# =============================================================================
# Violation Reasons
# =============================================================================

violation_reason := "insufficient_role" if {
    not allow
    not input.user.role in ["admin", "super_admin", "moderator"]
}

violation_reason := "mfa_required" if {
    not allow
    input.user.role in ["admin", "super_admin"]
    not mfa_verified
}

violation_reason := "business_hours_required" if {
    not allow
    sensitive_operation
    not business_hours
}

violation_reason := "ip_not_allowed" if {
    not allow
    not ip_allowed
}

violation_reason := "session_expired" if {
    not allow
    not session_valid
}

violation_reason := "operation_not_permitted" if {
    not allow
    not admin_operation_allowed
    not moderator_resource_allowed
}