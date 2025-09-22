# DuckBot Security Integration Guide

## Quick Start

### 1. Installation and Setup

```bash
# Navigate to DuckBot directory
cd DuckBot-Consolidated-v4.2

# Install required dependencies
pip install pydantic bcrypt pyotp qrcode aiofiles aiohttp

# Verify security configuration
python duckbot/tools/security_manager.py config show
```

### 2. Basic Integration

```python
# Import security integration
from duckbot.core.security_integration import SecurityIntegration

# Initialize security system
security_integration = SecurityIntegration()
await security_integration.initialize()

# Start background tasks
await security_integration.start_background_tasks()
```

### 3. User Authentication

```python
# Authenticate user
context = await security_integration.authenticate(
    username="admin",
    password="secure_password",
    ip_address="192.168.1.100"
)

if context:
    print(f"Welcome {context.username}!")
    # Use context for permission checks
else:
    print("Authentication failed")
```

### 4. Protect DuckBot Components

```python
# Protect WebUI access
await security_integration.protect_webui_endpoint(
    endpoint_name="dashboard",
    required_permissions=[Permission.READ]
)

# Protect AI model access
await security_integration.protect_ai_model_access(
    model_name="gpt-4",
    required_permissions=[Permission.AI_MODEL_ACCESS]
)

# Protect desktop automation
await security_integration.protect_desktop_automation(
    action_name="file_operations",
    required_permissions=[Permission.DESKTOP_AUTOMATION]
)
```

## Integration Examples

### 1. WebUI Security Integration

```python
from fastapi import FastAPI, HTTPException, Depends
from duckbot.core.security_integration import SecurityIntegration, Permission

app = FastAPI()
security = SecurityIntegration()

@app.on_event("startup")
async def startup_event():
    await security.initialize()
    await security.start_background_tasks()

@app.post("/auth/login")
async def login(username: str, password: str, ip_address: str = None):
    context = await security.authenticate(username, password, ip_address)
    if not context:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "session_id": context.session_id,
        "username": context.username,
        "access_token": security.security_manager.generate_jwt_token(context)
    }

@app.get("/dashboard")
@security.require_authentication
@security.require_permission(Permission.READ)
async def dashboard(security_context):
    return {"message": f"Welcome to your dashboard, {security_context.username}!"}

@app.get("/admin/users")
@security.require_authentication
@security.require_permission(Permission.USER_MANAGEMENT)
async def admin_users(security_context):
    return {"message": "User management panel"}
```

### 2. API Security Integration

```python
from fastapi import FastAPI, Header, HTTPException
from duckbot.core.security_integration import SecurityIntegration

app = FastAPI()
security = SecurityIntegration()

async def get_api_context(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    auth_result = await security.auth_system.authenticate_with_jwt(token)

    if not auth_result.success:
        raise HTTPException(status_code=401, detail="Invalid token")

    return auth_result

@app.get("/api/data")
async def get_data(context = Depends(get_api_context)):
    return {"data": "protected data", "user": context.username}

@app.post("/api/upload")
async def upload_file(
    file: UploadFile,
    context = Depends(get_api_context)
):
    # Validate file upload
    validation_result = await security.validate_file_upload(
        await file.read(),
        file.filename,
        file.content_type
    )

    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=validation_result.error_message
        )

    # Process file securely
    return {"message": "File uploaded successfully"}
```

### 3. Terminal Security Integration

```python
import asyncio
from duckbot.core.security_integration import SecurityIntegration, Permission

class SecureTerminal:
    def __init__(self):
        self.security = SecurityIntegration()

    async def execute_command(self, command: str, session_id: str):
        # Validate session
        context = await self.security.validate_session(session_id)
        if not context:
            return {"error": "Invalid session"}

        # Check permissions
        if not await self.security.check_permission(
            session_id, Permission.EXECUTE, ResourceType.TERMINAL_COMMAND
        ):
            return {"error": "Insufficient permissions"}

        # Validate and sanitize command
        validation_result = await self.security.validate_and_sanitize_input(
            command, InputType.COMMAND
        )

        if not validation_result.is_valid:
            return {"error": validation_result.error_message}

        # Execute command safely
        safe_command = validation_result.sanitized_value
        result = await self._execute_safe_command(safe_command)

        # Log command execution
        await self.security.log_security_event(
            SecurityEventType.DATA_ACCESS,
            user_id=context.user_id,
            username=context.username,
            action=f"Executed command: {safe_command}",
            result="success"
        )

        return result

    async def _execute_safe_command(self, command: str):
        # Implement safe command execution
        return {"output": f"Command executed: {command}"}
```

### 4. Desktop Automation Security

```python
from duckbot.core.security_integration import SecurityIntegration, Permission

class SecureDesktopAutomation:
    def __init__(self):
        self.security = SecurityIntegration()

    async def automate_action(self, action: str, session_id: str):
        # Validate session
        context = await self.security.validate_session(session_id)
        if not context:
            return {"error": "Invalid session"}

        # Check desktop automation permissions
        if not await self.security.check_permission(
            session_id, Permission.DESKTOP_AUTOMATION
        ):
            return {"error": "Desktop automation not permitted"}

        # Validate action
        validation_result = await self.security.validate_and_sanitize_input(
            action, InputType.TEXT
        )

        if not validation_result.is_valid:
            return {"error": validation_result.error_message}

        # Execute automation safely
        result = await self._execute_automation(action)

        # Log automation action
        await self.security.log_security_event(
            SecurityEventType.DATA_MODIFICATION,
            user_id=context.user_id,
            username=context.username,
            action=f"Desktop automation: {action}",
            result="success"
        )

        return result

    async def _execute_automation(self, action: str):
        # Implement safe automation execution
        return {"result": f"Automation completed: {action}"}
```

## Security Decorators

### Authentication Required

```python
@security_integration.require_authentication
async def protected_function(security_context, **kwargs):
    # User is authenticated
    return {"user": security_context.username}
```

### Permission Required

```python
@security_integration.require_permission(Permission.ADMIN)
async def admin_function(security_context, **kwargs):
    # User has admin permission
    return {"message": "Admin access granted"}
```

### Combined Protection

```python
@security_integration.require_authentication
@security_integration.require_permission(Permission.WRITE)
async def update_data(security_context, data: dict):
    # User is authenticated and has write permission
    return {"message": "Data updated successfully"}
```

## Security Best Practices

### 1. Always Validate Input

```python
# GOOD: Validate input
validation_result = await security.validate_and_sanitize_input(
    user_input, InputType.TEXT
)
if validation_result.is_valid:
    safe_input = validation_result.sanitized_value
    # Process safe_input

# BAD: Direct use of user input
process(user_input)  # Security risk!
```

### 2. Use Proper Authentication

```python
# GOOD: Use authentication decorator
@security_integration.require_authentication
async def protected_function(security_context):
    return {"data": "protected"}

# BAD: No authentication check
async def unprotected_function():
    return {"data": "exposed"}  # Security risk!
```

### 3. Log Security Events

```python
# Log important security events
await security.log_security_event(
    SecurityEventType.USER_CREATE,
    user_id=new_user_id,
    username=username,
    action="Created new user account",
    result="success"
)
```

### 4. Handle Errors Securely

```python
# GOOD: Secure error handling
try:
    result = await secure_operation()
except SecurityException as e:
    # Log security error
    await security.log_security_event(
        SecurityEventType.SECURITY_CONFIG_CHANGE,
        action=f"Security error: {str(e)}",
        result="failure"
    )
    # Return generic error message
    return {"error": "Operation failed"}

# BAD: Expose sensitive information
except Exception as e:
    return {"error": f"Detailed error: {str(e)}"}  # Information disclosure!
```

## Security Testing

### 1. Authentication Testing

```python
# Test valid authentication
context = await security.authenticate("valid_user", "valid_password")
assert context is not None

# Test invalid authentication
context = await security.authenticate("invalid_user", "wrong_password")
assert context is None

# Test session validation
valid = await security.validate_session(context.session_id)
assert valid is True
```

### 2. Permission Testing

```python
# Test permission check
has_permission = await security.check_permission(
    session_id, Permission.READ
)
assert has_permission is True

# Test insufficient permissions
has_permission = await security.check_permission(
    session_id, Permission.ADMIN
)
assert has_permission is False
```

### 3. Input Validation Testing

```python
# Test valid input
result = await security.validate_and_sanitize_input(
    "normal_text", InputType.TEXT
)
assert result.is_valid is True

# Test malicious input
result = await security.validate_and_sanitize_input(
    "<script>alert('xss')</script>", InputType.HTML
)
assert result.is_valid is False
```

## Monitoring and Alerting

### 1. Security Status Monitoring

```python
# Get security status
status = await security.get_security_status()
print(f"Security enabled: {status['security_enabled']}")
print(f"Active sessions: {status['active_sessions']}")
print(f"Recent threats: {status['recent_threats']}")
```

### 2. Alert Handling

```python
def handle_security_alert(alert):
    print(f"SECURITY ALERT: {alert.title}")
    print(f"Severity: {alert.severity}")
    print(f"Description: {alert.description}")

    # Take appropriate action based on severity
    if alert.severity in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
        # Immediate action required
        pass

# Register alert handler
security.security_monitor.add_alert_handler(handle_security_alert)
```

### 3. Compliance Reporting

```python
from datetime import datetime, timedelta
from duckbot.core.audit_logger import ComplianceStandard

# Generate compliance report
period_start = datetime.utcnow() - timedelta(days=30)
period_end = datetime.utcnow()

report = await security.generate_compliance_report(
    ComplianceStandard.GDPR,
    period_start,
    period_end
)

print(f"Compliance score: {report.compliance_score}%")
print(f"Total events: {report.total_events}")
print(f"Security events: {report.security_events}")
```

## Troubleshooting

### 1. Common Integration Issues

**Authentication not working:**
```bash
# Check security configuration
python duckbot/tools/security_manager.py config show

# Verify users exist
python duckbot/tools/security_manager.py user list

# Check audit logs for errors
python duckbot/tools/security_manager.py audit view --hours 1
```

**Permissions not working:**
```bash
# Check user roles
python duckbot/tools/security_manager.py user list

# Verify role permissions
python duckbot/tools/security_manager.py role list

# Check component protection
python duckbot/tools/security_manager.py monitor status
```

**Performance issues:**
```bash
# Check system metrics
python duckbot/tools/security_manager.py monitor metrics

# Monitor active sessions
python duckbot/tools/security_manager.py monitor status

# Review rate limiting settings
python duckbot/tools/security_manager.py config show | grep rate_limiting
```

### 2. Debug Mode

Enable debug mode for detailed logging:

```python
# Enable debug mode
security_integration.config["security_framework"]["debug_mode"] = True

# Or use environment variable
import os
os.environ["SECURITY_DEBUG_MODE"] = "true"
```

### 3. Security Health Check

```python
async def security_health_check():
    """Perform comprehensive security health check"""

    # Check security status
    status = await security.get_security_status()

    # Check authentication
    auth_test = await security.authenticate("test_user", "test_password")

    # Check permissions
    perm_test = await security.check_permission("test_session", Permission.READ)

    # Check input validation
    input_test = await security.validate_and_sanitize_input("test", InputType.TEXT)

    # Generate health report
    health_report = {
        "security_enabled": status["security_enabled"],
        "authentication_works": auth_test is not None,
        "permissions_works": perm_test,
        "input_validation_works": input_test.is_valid,
        "active_sessions": status["active_sessions"],
        "protected_components": status["components_protected"]
    }

    return health_report
```

This integration guide provides practical examples for implementing security in DuckBot components. Always follow security best practices and regularly review your security implementation.