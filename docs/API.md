# AiFinPay Autonomous OS API Documentation

## Overview

The AiFinPay Autonomous OS API provides endpoints for payment processing, content approvals, MCP/x402 integration, and system health monitoring with JWT-based authentication and role-based access control.

**Base URL**: `http://localhost:8000` (development)  
**API Version**: `1.0.0`  
**Documentation**: `/docs` (Swagger UI)  
**OpenAPI Spec**: `/openapi.json`

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

### Token Creation

Tokens are created using the `create_access_token` function from `apps/api/auth.py`:

```python
from apps.api.auth import create_access_token
from datetime import timedelta

# Create token with 30-minute expiration
token = create_access_token(
    data={"sub": "user_id", "role": "operator"},
    expires_delta=timedelta(minutes=30)
)
```

### Roles and Permissions

The API implements role-based access control (RBAC) with three roles:

| Role      | Permissions                      | Description                     |
|-----------|----------------------------------|---------------------------------|
| `admin`   | read, write, approve, execute    | Full system access              |
| `operator`| read, write, approve               | Content and payment management  |
| `viewer`  | read                              | Read-only access                |

### Role Dependencies

- `require_admin`: Requires admin role (read, write, approve, execute)
- `require_operator`: Requires operator role (read, write, approve)  
- `require_viewer`: Requires viewer role (read)

## API Endpoints

### System Endpoints

#### Health Check
- **Endpoint**: `GET /health`
- **Authentication**: None
- **Description**: System health check with dependency status
- **Response**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy"
  }
}
```

#### System Metrics
- **Endpoint**: `GET /api/v1/metrics`
- **Authentication**: None
- **Description**: System-wide metrics and statistics
- **Response**:
```json
{
  "agents": 5,
  "tasks": {"pending": 3, "succeeded": 45, "failed": 2},
  "campaigns": 12,
  "sources": 25,
  "recent_activity": [...]
}
```

#### List Agents
- **Endpoint**: `GET /api/v1/agents`
- **Authentication**: None
- **Description**: List all available agents with capabilities
- **Response**:
```json
[
  {
    "name": "Growth Orchestrator",
    "role": "orchestrator",
    "description": "Coordinates growth strategies",
    "capabilities": ["analyze", "plan", "execute"]
  }
]
```

### Payments Endpoints

#### Create Payment
- **Endpoint**: `POST /api/v1/payments/`
- **Authentication**: `require_operator`
- **Description**: Create a new payment request with automatic approval for small amounts
- **Request**:
```json
{
  "recipient_address": "0x71ce0fb1a99dcc187fe86cefb9fba7c12082ac03",
  "amount": 10.0,
  "currency": "SOL",
  "network": "solana",
  "purpose": "Test payment"
}
```
- **Response**: `201 Created` with payment details

#### List Payments
- **Endpoint**: `GET /api/v1/payments/`
- **Authentication**: `require_viewer`
- **Description**: Retrieve paginated list of all payment records
- **Response**: `200 OK` with array of payment objects

#### Approve Payment
- **Endpoint**: `POST /api/v1/payments/{payment_id}/approve`
- **Authentication**: `require_operator`
- **Description**: Approve a pending payment for execution
- **Request**:
```json
{
  "approved_by": "operator_user"
}
```
- **Response**: `200 OK` with updated payment details

#### Execute Payment
- **Endpoint**: `POST /api/v1/payments/{payment_id}/execute`
- **Authentication**: `require_admin`
- **Description**: Execute an approved payment transaction
- **Response**: `200 OK` with execution results

### Approvals Endpoints

#### List Content Queue
- **Endpoint**: `GET /api/v1/content`
- **Authentication**: `require_viewer`
- **Description**: Returns content items ordered by status for the approval queue
- **Response**: `200 OK` with array of content items

#### Edit Content
- **Endpoint**: `PATCH /api/v1/content/{content_id}`
- **Authentication**: `require_operator`
- **Description**: Edit content item (title, body, variants). Resets status to draft
- **Request**:
```json
{
  "title": "Updated Title",
  "body": "Updated content body"
}
```
- **Response**: `200 OK` with updated content

#### Approve Content
- **Endpoint**: `POST /api/v1/content/{content_id}/approve`
- **Authentication**: `require_operator`
- **Description**: Approve content item and set scheduled date
- **Request**:
```json
{
  "approved_by": "operator_user",
  "expires_in_hours": 24
}
```
- **Response**: `200 OK` with approval details

#### Publish Content
- **Endpoint**: `POST /api/v1/content/{content_id}/publish`
- **Authentication**: `require_admin`
- **Description**: Enqueue approved content for publishing to external platforms
- **Response**: `200 OK` with enqueue confirmation

#### List Approvals
- **Endpoint**: `GET /api/v1/approvals`
- **Authentication**: `require_viewer`
- **Description**: Retrieve list of all approval records
- **Response**: `200 OK` with array of approval objects

## Error Responses

The API uses standard HTTP status codes:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message description"
}
```

## Interactive Documentation

### Swagger UI
Access the interactive API documentation at:
- **Development**: `http://localhost:8000/docs`
- **Staging**: `https://staging.aifinpay.io/docs`

### OpenAPI Specification
The complete OpenAPI specification is available at:
- **Development**: `http://localhost:8000/openapi.json`
- **Staging**: `https://staging.aifinpay.io/openapi.json`
- **Static**: `docs/openapi.json` (committed to repository)

## Security Features

### Payment Safety Controls
- **Kill Switch**: Emergency payment disablement
- **Recipient Allowlist**: Restricted payment destinations
- **Spending Limits**: Per-transaction and daily spending caps
- **Human Approval Threshold**: Manual approval for large amounts

### Authentication
- JWT-based authentication with role-based access control
- Token expiration and validation
- Secure endpoint protection by role

## Testing

### Authentication Testing
Use the `create_test_token` function from `apps/api/auth.py` for testing:

```python
from apps.api.auth import create_test_token

# Create test tokens
admin_token = create_test_token(role="admin")
operator_token = create_test_token(role="operator")
viewer_token = create_test_token(role="viewer")
```

### Example Requests

#### With Authentication
```bash
# Create payment with operator token
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Authorization: Bearer <operator_token>" \
  -H "Content-Type: application/json" \
  -d '{"recipient_address": "0x71ce...", "amount": 10.0, "currency": "SOL", "network": "solana", "purpose": "Test"}'
```

#### Without Authentication (Expected 401)
```bash
curl -X GET http://localhost:8000/api/v1/payments/
# Returns 401 Unauthorized
```

## Rate Limiting and Performance

The API has been tested under high load (150 concurrent users) with:
- **Success Rate**: 99.19%
- **Average Response Time**: 1.5s (p50), 8.5s (p95)
- **Throughput**: 23.45 requests/second under load

## Monitoring

### Health Endpoints
- `/health`: System health check
- `/api/v1/metrics`: System metrics
- `/api/v1/audit`: Recent audit events

### Logging
Application logs are available in the `logs/` directory with detailed request/response information and security events.