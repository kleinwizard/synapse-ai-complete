# Comprehensive Logging Guide for Synapse AI

This guide explains the comprehensive logging system implemented throughout the Synapse AI application to help debug issues like the "malicious content" error and provide complete visibility into the application flow.

## Overview

The logging system provides structured, searchable logs across all application components with the following features:

- **Structured JSON logging** for easy parsing and analysis
- **Request tracing** with unique IDs across the entire request lifecycle
- **Performance monitoring** with execution time tracking
- **Security event logging** for malicious content detection and auth events
- **Database query logging** with execution time and parameter tracking
- **External API call logging** for OpenAI/Anthropic integrations
- **Frontend error tracking** with React error boundaries
- **User action logging** for complete user journey tracking

## Backend Logging (Python FastAPI)

### Configuration

The backend uses a centralized logging configuration in `app/logging_config.py`:

```python
# Environment variables for logging control
LOG_LEVEL=INFO                    # DEBUG, INFO, WARN, ERROR
LOG_FORMAT=json                   # json or text
LOG_FILE=synapse_ai.log          # Log file name
```

### Key Features

#### 1. Request/Response Middleware
Every HTTP request is logged with:
- Unique request ID for tracing
- Full request details (method, path, headers, body)
- Response status and body
- Execution time
- User context (email, user ID)
- IP address and user agent

#### 2. Database Logging
All database operations are logged including:
- SQL queries (sanitized)
- Execution time
- Connection pool status
- Slow queries (>1 second)
- Connection events

#### 3. Validation Logging
Content validation captures:
- All content being validated
- Specific patterns detected
- Validation results and reasons
- **Exact details when "malicious content" is flagged**

Example validation log:
```json
{
  "timestamp": "2025-08-08T12:34:56Z",
  "level": "WARNING",
  "event_type": "validation_failure",
  "validation_type": "xss_detection",
  "reason": "Pattern 1: <script[^>]*>.*?</script> matched: <script>alert('xss')</script>",
  "content_preview": "User input with <script>alert('xss')</script> detected",
  "user_email": "user@example.com",
  "request_id": "req_1725792896_abc123"
}
```

#### 4. Authentication Logging
Comprehensive auth event tracking:
- Login attempts (success/failure)
- Password verification
- Token creation and validation
- JWT errors
- Rate limiting violations

#### 5. External API Logging
Detailed logging of all LLM API calls:
- Request data (sanitized)
- Response data
- Execution time
- Token usage
- Errors and retries
- Provider-specific details

## Frontend Logging (React/TypeScript)

### Configuration

Frontend logging is configured via environment variables:

```bash
VITE_ENABLE_LOGGING=true
VITE_LOG_LEVEL=INFO
VITE_LOGGING_ENDPOINT=/api/logs
```

### Key Features

#### 1. API Call Logging
Every API request includes:
```typescript
logger.info(`API call started: POST /optimize`, EventType.API_CALL_START, {
  endpoint: '/optimize',
  method: 'POST',
  request_id: 'req_1725792896_xyz789',
  request_data: { /* sanitized request data */ },
  has_auth_token: true,
  timeout: 60000,
  retries: 2
});
```

#### 2. Error Boundary Logging
React component errors are automatically captured:
```typescript
logger.error('React component error caught by ErrorBoundary', EventType.COMPONENT_ERROR, {
  error_id: 'error_1725792896_def456',
  error_message: 'Cannot read property of undefined',
  error_stack: '...',
  component_stack: '...',
  memory_usage: { /* performance.memory info */ },
  url: window.location.href
});
```

#### 3. User Action Logging
All user interactions are tracked:
```typescript
logger.logUserAction('form_submit', {
  form_name: 'optimize_prompt',
  form_data: { /* sanitized form data */ },
  validation_errors: []
});
```

## Infrastructure Logging

### Nginx Access Logs

Enhanced nginx logging with multiple formats:

#### JSON Structured Format
```json
{
  "timestamp": "2025-08-08T12:34:56Z",
  "remote_addr": "192.168.1.100",
  "method": "POST",
  "uri": "/api/optimize",
  "status": 200,
  "response_time": 2.345,
  "upstream_response_time": "2.123",
  "http_x_request_id": "req_1725792896_abc123",
  "http_user_agent": "Mozilla/5.0...",
  "request_size": 1024,
  "response_size": 4096
}
```

#### Security Format (for auth endpoints)
Logs additional security context for authentication endpoints.

#### Performance Format
Focuses on timing metrics for performance analysis.

### Docker Logging

All services use structured Docker logging:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "200m"
    max-file: "10"
    labels: "service=backend,environment=production,component=api"
```

### Database Logging

PostgreSQL is configured with comprehensive logging:
- All SQL statements
- Connection events
- Long-running queries (>1 second)
- Lock waits
- Checkpoint events

## Debugging the "Malicious Content" Error

When a "malicious content" error occurs, follow this debugging process:

### 1. Find the Request ID
Look for the request ID in the error response or frontend logs.

### 2. Backend Validation Logs
Search for validation events:
```bash
grep "validation_failure" /var/log/synapse/synapse_ai.log | grep "req_1725792896_abc123"
```

This will show:
- Exact content that was flagged
- Which validation pattern matched
- The specific regex that triggered the detection
- User context and timing

### 3. Check API Call Logs
Trace the full request lifecycle:
```bash
grep "req_1725792896_abc123" /var/log/synapse/synapse_ai.log
```

### 4. Frontend Error Logs
Check browser console or frontend logs for client-side context.

### 5. Nginx Access Logs
Verify request routing and timing:
```bash
grep "req_1725792896_abc123" /var/log/nginx/api.log
```

## Log Analysis and Monitoring

### Searching Logs

#### By Request ID
```bash
# All logs for a specific request
grep "req_1725792896_abc123" /var/log/synapse/*.log

# Just validation events
jq 'select(.event_type == "validation_failure")' /var/log/synapse/synapse_ai.log
```

#### By User
```bash
# All events for a specific user
jq 'select(.user_email == "user@example.com")' /var/log/synapse/synapse_ai.log
```

#### By Event Type
```bash
# All malicious content detections
jq 'select(.event_type == "validation_failure")' /var/log/synapse/synapse_ai.log

# All API call errors
jq 'select(.event_type == "api_call_error")' /var/log/synapse/synapse_ai.log
```

### Performance Analysis

#### Slow Requests
```bash
# API calls taking more than 5 seconds
jq 'select(.execution_time_seconds > 5)' /var/log/synapse/synapse_ai.log
```

#### Database Performance
```bash
# Slow database queries
jq 'select(.event_type == "db_slow_query")' /var/log/synapse/synapse_ai.log
```

## Log File Locations

### Development
- Backend: Console output and `synapse_ai.log`
- Frontend: Browser console
- Database: Docker logs

### Production (Docker)
- Backend: `/var/log/synapse/synapse_ai.log`
- Nginx: `/var/log/nginx/*.log`
- Database: Docker logs via `docker logs synapse_db`
- All services: `docker logs <service_name>`

### Docker Volume Mounts
```bash
# View API logs
docker exec synapse_api cat /app/logs/synapse_ai.log

# View nginx logs
docker exec synapse_nginx cat /var/log/nginx/access.log

# View all logs for a service
docker logs synapse_api --follow
```

## Log Retention and Rotation

### File-based Logs
- **Rotation**: 10MB max size, 5 backup files
- **Retention**: ~50MB total per service
- **Format**: JSON for structured analysis

### Docker Logs
- **Size**: 100-500MB max per service
- **Files**: 3-10 backup files
- **Labels**: Service, environment, component tags

## Security Considerations

### Sensitive Data Protection
All logging components automatically sanitize:
- Passwords and API keys
- Authorization tokens
- Personal data beyond email/username
- Long content (truncated with markers)

### Log Access
- Production logs require appropriate server access
- Structured format enables secure log forwarding
- Request IDs allow tracing without exposing sensitive data

## Troubleshooting Common Issues

### High Log Volume
Adjust log levels:
```bash
# Reduce verbosity
export LOG_LEVEL=WARN

# Development debugging
export LOG_LEVEL=DEBUG
```

### Missing Request Context
Ensure middleware is properly configured:
1. Logging middleware loads first
2. Request context is set for all requests
3. User information is available from authentication

### Log Parsing Issues
Use `jq` for JSON log parsing:
```bash
# Pretty print logs
cat synapse_ai.log | jq '.'

# Filter by level
cat synapse_ai.log | jq 'select(.level == "ERROR")'
```

## Integration with Monitoring Tools

The structured JSON logging format integrates with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Prometheus** + **Grafana**
- **DataDog**
- **New Relic**
- **Splunk**

Example Logstash configuration is provided in `docker-compose.prod.yml` (commented out).

## Getting Help

When reporting issues, include:
1. **Request ID** from error or logs
2. **Timestamp** of the issue
3. **User email** (if known)
4. **Relevant log excerpts** showing the error flow

The comprehensive logging system ensures that any issue can be traced from the initial user action through all backend processing to the final response.