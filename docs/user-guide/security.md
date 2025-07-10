# Security Guide

MetaMCP implements comprehensive security features to protect your AI agent infrastructure and data.

## Security Overview

MetaMCP provides multiple layers of security:

- **Authentication**: JWT tokens and OAuth integration
- **Authorization**: Role-based access control with OPA
- **Audit Logging**: Complete request tracking
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Protection against abuse
- **Encryption**: Secure data transmission and storage

## Authentication

### JWT Authentication

MetaMCP uses JWT (JSON Web Tokens) for stateless authentication:

```bash
# Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# Use token in requests
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/tools
```

#### JWT Configuration

```env
# JWT Settings
SECRET_KEY=your-secure-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Security Best Practices

1. **Use strong secret keys**: Generate cryptographically secure random keys
2. **Rotate secrets regularly**: Change JWT secrets periodically
3. **Set appropriate expiration**: Balance security with user experience
4. **Use HTTPS**: Always use HTTPS in production

### OAuth Authentication

MetaMCP supports OAuth 2.0 with multiple providers:

#### Google OAuth

```env
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
```

#### GitHub OAuth

```env
GITHUB_OAUTH_CLIENT_ID=your-github-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-github-client-secret
```

#### Microsoft OAuth

```env
MICROSOFT_OAUTH_CLIENT_ID=your-microsoft-client-id
MICROSOFT_OAUTH_CLIENT_SECRET=your-microsoft-client-secret
```

#### OAuth Flow

1. **Initiate login**:
   ```bash
   GET /api/oauth/login/google
   ```

2. **User redirected** to OAuth provider

3. **Callback handling**:
   ```bash
   GET /api/oauth/callback/google?code=<auth_code>
   ```

4. **JWT token returned** for API access

## Authorization

### Role-Based Access Control (RBAC)

MetaMCP implements RBAC with the following roles:

- **admin**: Full system access
- **user**: Standard user access
- **agent**: AI agent access
- **readonly**: Read-only access

#### Permission System

```python
# Permission examples
permissions = [
    "tool:read",      # View tools
    "tool:write",     # Create/update tools
    "tool:execute",   # Execute tools
    "user:read",      # View users
    "user:write",     # Create/update users
    "policy:read",    # View policies
    "policy:write",   # Create/update policies
    "system:admin"    # Administrative access
]
```

#### Checking Permissions

```python
from metamcp.auth import check_permission

# Check if user can execute tool
if check_permission(user, "tool:execute", tool_id):
    # Execute tool
    result = execute_tool(tool_id, arguments)
```

### Open Policy Agent (OPA) Integration

MetaMCP uses OPA for advanced policy enforcement:

#### Policy Examples

**Tool Access Policy** (`policies/tool_access.rego`):
```rego
package tool_access

# Allow tool execution if user has permission
allow {
    input.action == "execute"
    input.user.roles[_] == "admin"
}

allow {
    input.action == "execute"
    input.user.roles[_] == "user"
    input.user.permissions[_] == "tool:execute"
}

# Deny access to high-security tools
deny {
    input.action == "execute"
    input.tool.security_level > 2
    input.user.roles[_] != "admin"
}
```

**Admin Access Policy** (`policies/admin_access.rego`):
```rego
package admin_access

# Only admins can access admin functions
allow {
    input.action == "admin"
    input.user.roles[_] == "admin"
}

# Deny all other admin access
deny {
    input.action == "admin"
    not input.user.roles[_] == "admin"
}
```

#### Policy Evaluation

```python
from metamcp.policy import evaluate_policy

# Evaluate tool access
result = evaluate_policy("tool_access", {
    "user": user,
    "action": "execute",
    "tool": tool,
    "resource": f"tool:{tool.id}"
})

if result.get("allow"):
    # Execute tool
    pass
else:
    # Deny access
    raise PermissionError("Access denied")
```

## Audit Logging

MetaMCP provides comprehensive audit logging:

### Logged Events

- **Authentication**: Login/logout attempts
- **Authorization**: Permission checks and denials
- **Tool Operations**: Registration, execution, updates
- **System Events**: Configuration changes, health checks
- **Security Events**: Failed login attempts, suspicious activity

### Audit Log Format

```json
{
  "timestamp": "2025-07-10T19:30:00Z",
  "event_type": "tool_execution",
  "user_id": "user123",
  "tool_id": "calculator-abc123",
  "action": "execute",
  "result": "success",
  "ip_address": "192.168.1.100",
  "user_agent": "MetaMCP-Client/1.0",
  "execution_time": 0.15,
  "metadata": {
    "arguments": {"expression": "2 + 2"},
    "result": {"value": 4}
  }
}
```

### Audit Log Configuration

```env
# Audit logging settings
AUDIT_LOG_ENABLED=true
AUDIT_LOG_LEVEL=INFO
AUDIT_LOG_RETENTION_DAYS=90
AUDIT_LOG_ENCRYPTION=true
```

## Input Validation

### Request Validation

MetaMCP validates all incoming requests:

```python
from pydantic import BaseModel, validator

class ToolExecutionRequest(BaseModel):
    tool_id: str
    arguments: dict
    timeout: Optional[int] = 30
    
    @validator('tool_id')
    def validate_tool_id(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Tool ID must be at least 3 characters')
        return v
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v and (v < 1 or v > 300):
            raise ValueError('Timeout must be between 1 and 300 seconds')
        return v
```

### SQL Injection Prevention

MetaMCP uses parameterized queries:

```python
# Safe query execution
async def get_tool_by_id(tool_id: str):
    query = "SELECT * FROM tools WHERE id = :tool_id"
    result = await database.fetch_one(query, {"tool_id": tool_id})
    return result
```

### XSS Prevention

MetaMCP sanitizes user input:

```python
import html

def sanitize_input(user_input: str) -> str:
    """Sanitize user input to prevent XSS"""
    return html.escape(user_input)
```

## Rate Limiting

### Rate Limit Configuration

```env
# Rate limiting settings
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
RATE_LIMIT_BURST=10
```

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Rate Limit Implementation

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/tools/{tool_id}/execute")
@limiter.limit("100/minute")
async def execute_tool(request: Request, tool_id: str):
    # Tool execution logic
    pass
```

## Data Protection

### Encryption at Rest

MetaMCP supports encryption for sensitive data:

```env
# Encryption settings
ENCRYPTION_ENABLED=true
ENCRYPTION_KEY=your-encryption-key
```

### Encryption in Transit

MetaMCP uses HTTPS/TLS for secure communication:

```python
# SSL/TLS configuration
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain("cert.pem", "key.pem")
```

### Data Sanitization

```python
def sanitize_tool_data(tool_data: dict) -> dict:
    """Remove sensitive information from tool data"""
    sanitized = tool_data.copy()
    
    # Remove sensitive fields
    sensitive_fields = ['api_key', 'password', 'secret']
    for field in sensitive_fields:
        if field in sanitized:
            del sanitized[field]
    
    return sanitized
```

## Security Headers

MetaMCP includes security headers:

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Security headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "*.example.com"]
)
```

## Security Monitoring

### Security Alerts

MetaMCP monitors for security events:

- **Failed login attempts**: Multiple failed logins
- **Suspicious activity**: Unusual access patterns
- **Rate limit violations**: Excessive API usage
- **Permission denials**: Repeated access denials

### Security Metrics

```python
# Security metrics
security_metrics = {
    "failed_logins": 0,
    "permission_denials": 0,
    "rate_limit_violations": 0,
    "suspicious_ips": set(),
    "last_security_alert": None
}
```

## Security Best Practices

### Development

1. **Use environment variables**: Never hardcode secrets
2. **Validate all input**: Implement comprehensive input validation
3. **Use HTTPS**: Always use HTTPS in production
4. **Regular updates**: Keep dependencies updated
5. **Security testing**: Implement security tests

### Production

1. **Strong secrets**: Use cryptographically secure random keys
2. **Regular rotation**: Rotate secrets and API keys regularly
3. **Monitoring**: Implement comprehensive security monitoring
4. **Backup security**: Secure backup procedures
5. **Incident response**: Have incident response procedures

### Network Security

1. **Firewall rules**: Restrict access to necessary ports
2. **VPN access**: Use VPN for administrative access
3. **Network segmentation**: Separate different environments
4. **DDoS protection**: Implement DDoS protection
5. **SSL/TLS**: Use strong SSL/TLS configuration

## Security Checklist

### Pre-Deployment

- [ ] All secrets configured via environment variables
- [ ] HTTPS enabled and properly configured
- [ ] Firewall rules configured
- [ ] Rate limiting enabled
- [ ] Audit logging enabled
- [ ] Security headers configured
- [ ] Input validation implemented
- [ ] SQL injection prevention in place
- [ ] XSS prevention implemented

### Post-Deployment

- [ ] Security monitoring enabled
- [ ] Regular security scans scheduled
- [ ] Backup procedures tested
- [ ] Incident response plan documented
- [ ] Security team notified
- [ ] Access logs monitored
- [ ] Failed login attempts tracked
- [ ] Suspicious activity alerts configured

## Security Incident Response

### Incident Classification

1. **Low**: Failed login attempts, minor rate limit violations
2. **Medium**: Unauthorized access attempts, suspicious activity
3. **High**: Data breach, system compromise
4. **Critical**: Complete system compromise, data exfiltration

### Response Procedures

1. **Detection**: Automated monitoring detects incident
2. **Assessment**: Evaluate severity and impact
3. **Containment**: Isolate affected systems
4. **Investigation**: Determine root cause
5. **Remediation**: Fix vulnerabilities
6. **Recovery**: Restore normal operations
7. **Documentation**: Document lessons learned

### Contact Information

- **Security Team**: security@example.com
- **Emergency**: +1-555-0123
- **Incident Response**: https://example.com/security/incident 