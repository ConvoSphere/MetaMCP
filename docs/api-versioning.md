# API Versioning System

## Overview

The MetaMCP API implements a comprehensive versioning system that allows for backward compatibility while introducing new features and improvements. This system ensures that existing clients continue to work while new clients can take advantage of enhanced functionality.

## Version Management

### Current Versions

- **v1**: Initial API version with core functionality
- **v2**: Enhanced API version with improved features and new endpoints

### Version Status

Each API version has one of three statuses:

- **ACTIVE**: Fully supported and recommended for new development
- **DEPRECATED**: Still functional but will be sunset in the future
- **SUNSET**: No longer available and will return 404 errors

## API Endpoints

### Version Information

#### List All Versions
```http
GET /api/versions
```

**Response:**
```json
{
  "versions": [
    {
      "version": "v1",
      "status": "active",
      "release_date": "2024-01-01T00:00:00Z",
      "description": "Initial API version with core functionality",
      "new_features": ["Basic authentication", "Tool management"],
      "is_deprecated": false,
      "is_sunset": false
    },
    {
      "version": "v2",
      "status": "active",
      "release_date": "2024-02-01T00:00:00Z",
      "description": "Enhanced API version with improved features",
      "new_features": ["Enhanced authentication", "Advanced analytics"],
      "breaking_changes": ["Changed response format for some endpoints"],
      "is_deprecated": false,
      "is_sunset": false
    }
  ],
  "latest_version": "v2",
  "active_versions": ["v1", "v2"]
}
```

#### Get Version Information
```http
GET /api/versions/{version}
```

#### Get Latest Version
```http
GET /api/versions/latest
```

### API Root
```http
GET /api
```

**Response:**
```json
{
  "message": "MetaMCP API",
  "latest_version": "v2",
  "active_versions": ["v1", "v2"],
  "documentation": "/docs",
  "version_info": "/api/versions"
}
```

### Latest Version Redirect
```http
GET /api/latest
```

Redirects to the latest API version.

## Version-Specific Endpoints

### v1 Endpoints

All existing endpoints are available under `/api/v1/`:

- `/api/v1/auth/*` - Authentication endpoints
- `/api/v1/tools/*` - Tool management
- `/api/v1/health/*` - Health checks
- `/api/v1/admin/*` - Admin interface
- `/api/v1/composition/*` - Workflow composition
- `/api/v1/oauth/*` - OAuth integration
- `/api/v1/proxy/*` - Proxy functionality

### v2 Endpoints

Enhanced endpoints available under `/api/v2/`:

- `/api/v2/auth/*` - Enhanced authentication with session management
- `/api/v2/tools/*` - Advanced tool management with improved search
- `/api/v2/health/*` - Comprehensive health checks with metrics
- `/api/v2/admin/*` - Enhanced admin interface
- `/api/v2/composition/*` - Improved workflow composition
- `/api/v2/analytics/*` - Advanced analytics and reporting

## Breaking Changes in v2

### Authentication Changes

**v1:**
```json
{
  "access_token": "token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**v2:**
```json
{
  "access_token": "token",
  "refresh_token": "refresh_token",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {...},
  "permissions": [...],
  "session_id": "session_id"
}
```

### Tool Creation Changes

**v1:**
```json
{
  "name": "tool_name",
  "description": "description",
  "endpoint": "https://example.com"
}
```

**v2:**
```json
{
  "name": "tool_name",
  "description": "description",
  "endpoint": "https://example.com",
  "security_level": 5,
  "rate_limit": 100,
  "timeout": 30
}
```

## Deprecation Headers

When using deprecated versions, the API includes deprecation headers:

```
X-API-Version-Deprecated: true
X-API-Version-Deprecation-Date: 2024-12-31T23:59:59Z
X-API-Version-Latest: v2
```

## Migration Guide

### From v1 to v2

1. **Update Authentication Flow**
   - Handle refresh tokens
   - Update token validation
   - Implement session management

2. **Update Tool Management**
   - Add security level assessment
   - Implement rate limiting
   - Add timeout configuration

3. **Update Health Checks**
   - Use enhanced health endpoints
   - Implement readiness/liveness checks
   - Add performance metrics

4. **Add Analytics**
   - Implement usage tracking
   - Add performance monitoring
   - Use error analytics

### Backward Compatibility

- v1 endpoints remain fully functional
- No breaking changes to existing v1 functionality
- Gradual migration path available
- Deprecation warnings provided

## Best Practices

### For API Consumers

1. **Always specify version in requests**
   ```http
   GET /api/v2/tools
   ```

2. **Handle deprecation headers**
   - Monitor for deprecation warnings
   - Plan migration to newer versions
   - Test with new versions before migration

3. **Use latest version for new development**
   - v2 is recommended for new projects
   - Take advantage of enhanced features
   - Better performance and security

### For API Developers

1. **Maintain backward compatibility**
   - Don't break existing functionality
   - Add new features incrementally
   - Provide migration paths

2. **Version management**
   - Clear deprecation timelines
   - Comprehensive documentation
   - Migration guides

3. **Testing**
   - Test all versions
   - Validate breaking changes
   - Ensure smooth transitions

## Configuration

### Environment Variables

```bash
# API Versioning
API_DEFAULT_VERSION=v1
API_LATEST_VERSION=v2
API_DEPRECATION_WARNING_DAYS=180
API_SUNSET_WARNING_DAYS=30
```

### Version Manager Settings

```python
# Initialize version manager
version_manager = get_api_version_manager()
await version_manager.initialize()

# Register new version
new_version = APIVersion(
    version="v3",
    status=VersionStatus.ACTIVE,
    release_date=datetime.utcnow(),
    description="New version with features"
)
version_manager.register_version(new_version)
```

## Monitoring and Analytics

### Version Usage Tracking

The system tracks:
- Version usage statistics
- Migration patterns
- Deprecation adoption
- Error rates by version

### Analytics Endpoints

```http
GET /api/v2/analytics/usage
GET /api/v2/analytics/performance
GET /api/v2/analytics/errors
```

## Future Roadmap

### Planned Versions

- **v3**: Advanced features and microservices architecture
- **v4**: GraphQL support and real-time capabilities

### Deprecation Timeline

- **v1**: Will be deprecated in Q4 2024, sunset in Q4 2025
- **v2**: Active until v3 release
- **v3**: Planned for Q1 2025

## Support

For questions about API versioning:

- Check the [API Documentation](/docs/api.md)
- Review [Migration Guides](/docs/migration.md)
- Contact the development team
- Monitor [Release Notes](/docs/releases.md)