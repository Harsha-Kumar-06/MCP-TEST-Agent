# Enterprise Deployment Guide - HelpDesk Bot

## Overview

This guide explains how to deploy the HelpDesk Bot for your organization with proper user authentication, audit logging, notification integrations, and security controls.

---

## Table of Contents

1. [Authentication Options](#authentication-options)
2. [Quick Start (Demo Mode)](#quick-start-demo-mode)
3. [Production Deployment](#production-deployment)
4. [SSO Integration](#sso-integration)
5. [LDAP/Active Directory](#ldapad-integration)
6. [Notification Integrations](#notification-integrations)
7. [Audit & Compliance](#audit--compliance)
8. [Security Hardening](#security-hardening)
9. [Scaling & High Availability](#scaling--high-availability)

> 📖 **For initial setup**, see [SETUP_GUIDE.md](SETUP_GUIDE.md) first.

---

## Authentication Options

| Method | Use Case | Complexity |
|--------|----------|------------|
| **Basic Auth** | Development, small teams | Low |
| **LDAP/AD** | Enterprise with Active Directory | Medium |
| **SSO/SAML** | Okta, Azure AD, OneLogin | Medium |
| **OAuth 2.0** | Google Workspace, Microsoft 365 | Medium |

---

## Quick Start (Demo Mode)

### 1. No Authentication (Development)

By default, authentication is disabled:

```bash
# .env file
REQUIRE_AUTH=false
GOOGLE_API_KEY=your_gemini_api_key

# Run the server
python app.py
```

### 2. Basic Authentication (Demo)

Enable basic auth with demo users:

```bash
# .env file
REQUIRE_AUTH=true
AUTH_METHOD=basic
GOOGLE_API_KEY=your_gemini_api_key
```

Demo credentials:
| Email | Password | Role |
|-------|----------|------|
| john.doe@company.com | demo123 | Employee |
| jane.smith@company.com | demo123 | Manager |
| admin@company.com | admin123 | Admin |

---

## Production Deployment

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (HTTPS)                     │
│                  (AWS ALB / Nginx / Cloudflare)             │
└────────────────────────────┬────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
    │ App 1   │         │ App 2   │         │ App 3   │
    │ FastAPI │         │ FastAPI │         │ FastAPI │
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
    │ Redis   │         │ ChromaDB│         │ Audit   │
    │ Sessions│         │ KB Store│         │ Logs    │
    └─────────┘         └─────────┘         └─────────┘
```

### Environment Variables

```bash
# .env (Production)

# === Authentication ===
REQUIRE_AUTH=true
AUTH_METHOD=sso                # basic, ldap, sso, oauth_google, oauth_microsoft

# === Google AI ===
GOOGLE_API_KEY=your_production_key

# === SSO (if using SSO) ===
SSO_ENABLED=true
SSO_PROVIDER=okta              # okta, azure, onelogin, google
SSO_ISSUER_URL=https://your-company.okta.com
SSO_CLIENT_ID=your_client_id
SSO_CLIENT_SECRET=your_client_secret

# === LDAP (if using LDAP) ===
LDAP_SERVER=ldap://ldap.company.com:389
LDAP_BASE_DN=dc=company,dc=com
LDAP_BIND_DN=cn=service,dc=company,dc=com
LDAP_BIND_PASSWORD=service_password

# === OAuth (if using OAuth) ===
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://helpdesk.company.com/api/auth/callback

# === Redis (Production Sessions) ===
REDIS_URL=redis://redis.company.com:6379
REDIS_PASSWORD=your_redis_password

# === Security ===
SECRET_KEY=your_256_bit_secret_key
ALLOWED_ORIGINS=https://helpdesk.company.com
```

---

## SSO Integration

### Okta Setup

1. **Create SAML Application in Okta**
   - Go to Applications → Create App Integration
   - Select SAML 2.0
   - Configure:
     - Single Sign-On URL: `https://helpdesk.company.com/api/auth/sso/callback`
     - Audience URI: `helpdesk-bot`

2. **Map User Attributes**
   ```
   email       → user.email
   firstName   → user.firstName
   lastName    → user.lastName
   department  → user.department
   employeeId  → user.employeeNumber
   ```

3. **Configure Environment**
   ```bash
   SSO_ENABLED=true
   SSO_PROVIDER=okta
   SSO_ISSUER_URL=https://your-company.okta.com
   SSO_CLIENT_ID=0oaxxxxxxxx
   ```

### Azure AD Setup

1. **Register Application in Azure Portal**
   - Azure Active Directory → App registrations → New registration
   - Configure redirect URI: `https://helpdesk.company.com/api/auth/callback`

2. **Configure Permissions**
   - API permissions → Add: `User.Read`, `profile`, `email`, `openid`

3. **Create Client Secret**
   - Certificates & secrets → New client secret

4. **Configure Environment**
   ```bash
   AUTH_METHOD=oauth_microsoft
   MICROSOFT_CLIENT_ID=your_app_id
   MICROSOFT_CLIENT_SECRET=your_secret
   MICROSOFT_TENANT_ID=your_tenant_id
   ```

---

## LDAP/AD Integration

### Configuration

```bash
# .env
AUTH_METHOD=ldap
LDAP_SERVER=ldap://dc1.company.com:389
LDAP_USE_SSL=true
LDAP_BASE_DN=dc=company,dc=com
LDAP_USER_FILTER=(sAMAccountName={username})
LDAP_BIND_DN=cn=helpdesk-svc,ou=ServiceAccounts,dc=company,dc=com
LDAP_BIND_PASSWORD=service_account_password
```

### Required LDAP Attributes

The system reads these attributes from LDAP:
- `mail` → email
- `displayName` → full_name
- `department` → department
- `employeeID` → employee_id
- `manager` → manager_email

### Testing LDAP Connection

```bash
# Test LDAP connectivity
python -c "
from auth import LDAPAuthProvider
ldap = LDAPAuthProvider()
user = ldap.authenticate({'username': 'jdoe', 'password': 'password'})
print(user)
"
```

---

## Notification Integrations

When users escalate to human specialists, the system can notify via multiple channels simultaneously.

### Overview

| Channel | Purpose | Setup Complexity |
|---------|---------|------------------|
| **Microsoft Teams** | Real-time channel notifications | Low (Webhooks) |
| **Email** | Direct specialist notification | Low (SMTP) |
| **ServiceNow** | Auto-create incidents/tickets | Medium (API) |

### Microsoft Teams Setup

1. **Create Incoming Webhooks** for each department channel in Teams
2. **Configure webhooks** in `.env`:

```env
ENABLE_NOTIFICATIONS=true
TEAMS_WEBHOOK_IT=https://yourcompany.webhook.office.com/webhookb2/xxx
TEAMS_WEBHOOK_HR=https://yourcompany.webhook.office.com/webhookb2/xxx
TEAMS_WEBHOOK_SALES=https://yourcompany.webhook.office.com/webhookb2/xxx
TEAMS_WEBHOOK_LEGAL=https://yourcompany.webhook.office.com/webhookb2/xxx
```

**Teams Notification Features:**
- Rich Adaptive Cards with issue details
- Action buttons (View Details, Join Chat)
- Color-coded urgency indicators
- Assignment information

### Email Setup

```env
# Microsoft 365
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=helpdesk@yourcompany.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=helpdesk@yourcompany.com
FROM_NAME=HelpDesk Bot
```

**Email Features:**
- HTML-formatted escalation emails
- Issue summary and priority
- Direct links to chat/ticket
- Plain text fallback

### ServiceNow Setup

1. **Create Integration User** in ServiceNow with `itil` and `rest_api_user` roles
2. **Configure** in `.env`:

```env
SERVICENOW_ENABLED=true
SERVICENOW_INSTANCE=https://yourcompany.service-now.com
SERVICENOW_USERNAME=integration_user
SERVICENOW_PASSWORD=your_password

# Assignment groups (match your ServiceNow group names)
SNOW_GROUP_IT=IT Support
SNOW_GROUP_HR=Human Resources
SNOW_GROUP_SALES=Sales Operations
SNOW_GROUP_LEGAL=Legal
```

**ServiceNow Features:**
- Auto-create incidents on escalation
- Correlation ID linking to chat session
- Priority/urgency mapping
- Assignment group routing
- Full conversation context in description

### Multi-Channel Notification Flow

When `escalate_to_human()` is called:

```
1. Create ServiceNow incident → INC0012345
2. Send Teams Adaptive Card → IT Support channel
3. Send Email → assigned_specialist@company.com
4. Return all references to user
```

**Response includes:**
```json
{
  "escalation_id": "ESC-20260211143022",
  "servicenow_incident": "INC0012345",
  "notifications_sent": {
    "servicenow": {"created": true, "incident_number": "INC0012345"},
    "teams": {"sent": true},
    "email": {"sent": true, "to": "specialist@company.com"}
  }
}
```

> 📖 **Detailed setup instructions:** See [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

## Audit & Compliance

### What Gets Logged

Every interaction is logged with:
- **Timestamp** - When the action occurred
- **User Identity** - Employee ID, email, department
- **Action Type** - chat_message, escalation, tool_use
- **Details** - Message content (truncated), response
- **IP Address** - Client IP for security tracking

### Log Format

```json
{
  "timestamp": "2026-02-09T10:15:30.123456",
  "employee_id": "EMP001",
  "email": "john.doe@company.com",
  "department": "Engineering",
  "action": "chat_message",
  "details": {
    "message": "How do I reset my password?",
    "response": "I found a KB article..."
  },
  "ip_address": "192.168.1.100"
}
```

### Integrating with SIEM

Modify `auth.py` to send logs to your SIEM:

```python
# For Splunk
import requests

def send_to_splunk(log_entry):
    requests.post(
        "https://splunk.company.com:8088/services/collector",
        headers={"Authorization": f"Splunk {SPLUNK_TOKEN}"},
        json={"event": log_entry}
    )

# For AWS CloudWatch
import boto3

def send_to_cloudwatch(log_entry):
    client = boto3.client('logs')
    client.put_log_events(
        logGroupName='/helpdesk-bot/audit',
        logStreamName='production',
        logEvents=[{
            'timestamp': int(time.time() * 1000),
            'message': json.dumps(log_entry)
        }]
    )
```

---

## Security Hardening

### 1. HTTPS Only

```nginx
# nginx.conf
server {
    listen 80;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/helpdesk.crt;
    ssl_certificate_key /etc/ssl/private/helpdesk.key;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Rate Limiting

```python
# Add to app.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("30/minute")
async def chat(...):
    ...
```

### 3. Input Validation

```python
# Add message length limits
class ChatMessage(BaseModel):
    message: str = Field(..., max_length=5000)
    session_id: str = None
```

### 4. Secrets Management

Use a secrets manager instead of .env files:

```python
# AWS Secrets Manager
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

secrets = get_secret('helpdesk-bot/production')
GOOGLE_API_KEY = secrets['GOOGLE_API_KEY']
```

---

## Scaling & High Availability

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helpdesk-bot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: helpdesk-bot
  template:
    metadata:
      labels:
        app: helpdesk-bot
    spec:
      containers:
      - name: helpdesk-bot
        image: your-registry/helpdesk-bot:latest
        ports:
        - containerPort: 8080
        env:
        - name: REQUIRE_AUTH
          value: "true"
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: helpdesk-secrets
              key: google-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: helpdesk-bot
spec:
  selector:
    app: helpdesk-bot
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

### Redis for Distributed Sessions

```python
# Replace InMemorySessionService with Redis
import redis

class RedisSessionService:
    def __init__(self):
        self.redis = redis.Redis.from_url(os.getenv("REDIS_URL"))
    
    async def create_session(self, app_name, user_id):
        session_id = str(uuid.uuid4())
        self.redis.hset(f"session:{session_id}", mapping={
            "app_name": app_name,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
        })
        self.redis.expire(f"session:{session_id}", 86400)  # 24 hours
        return {"id": session_id}
```

---

## Connecting Your Employee Directory

### Option 1: CSV Import

```python
# Import employees from CSV
import csv

def import_employees(csv_path):
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            MOCK_USERS[row['email']] = {
                "employee_id": row['employee_id'],
                "email": row['email'],
                "full_name": row['full_name'],
                "department": row['department'],
                "role": row.get('role', 'employee'),
                "manager_email": row.get('manager_email'),
                "password_hash": hashlib.sha256(row['password'].encode()).hexdigest(),
            }
```

### Option 2: Database Backend

```python
# Use PostgreSQL for user storage
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    
    employee_id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    full_name = Column(String)
    department = Column(String)
    role = Column(String)
    password_hash = Column(String)
```

### Option 3: HR System API Integration

```python
# Integrate with Workday, BambooHR, etc.
def fetch_employee_from_hr(email):
    response = requests.get(
        f"{HR_API_URL}/employees",
        params={"email": email},
        headers={"Authorization": f"Bearer {HR_API_TOKEN}"}
    )
    return response.json()
```

---

## Summary: Deployment Checklist

- [ ] Set `REQUIRE_AUTH=true` for production
- [ ] Choose authentication method (SSO/LDAP/OAuth)
- [ ] Configure identity provider integration
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set up audit log forwarding to SIEM
- [ ] Configure rate limiting
- [ ] Set up Redis for distributed sessions
- [ ] Deploy with multiple replicas for HA
- [ ] Configure health checks and monitoring
- [ ] Test failover scenarios
- [ ] Document runbook for operations team

---

## Support

For questions about enterprise deployment:
- Create an issue in your internal ticketing system
- Contact the AI Platform team
