# HelpDesk Bot - Organization Deployment Guide

A comprehensive guide to deploying and customizing the HelpDesk Bot Router Agent for your organization.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Integrating with Real Systems](#integrating-with-real-systems)
5. [Customization](#customization)
6. [Deployment Options](#deployment-options)
7. [Security Considerations](#security-considerations)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.10 or higher |
| Memory | Minimum 2GB RAM |
| Storage | 500MB for application |
| Network | Outbound HTTPS access to Google AI APIs |

### Required Accounts & Keys

1. **Google AI API Key** (Required)
   - Get from: https://aistudio.google.com/apikey
   - Free tier: 60 requests/minute
   - For production: Consider Vertex AI for enterprise features

2. **Optional Integrations**
   - ServiceNow API credentials (for IT ticketing)
   - Workday/SAP API access (for HR)
   - Salesforce API credentials (for CRM)
   - DocuSign API (for legal documents)

---

## Quick Start

### Step 1: Clone or Copy the Project

```bash
# Copy project to your server
git clone <your-repo-url> helpdesk-bot
cd helpdesk-bot
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# If venv is incomplete on Windows (missing activate.bat), use full Python path:
# C:\Python313\python.exe -m venv venv

# Activate (Windows CMD)
venv\Scripts\activate.bat

# Activate (Windows PowerShell)
venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Required `.env` contents:**
```env
# Google AI Configuration
GOOGLE_API_KEY=your_api_key_here

# Application Settings
APP_ENV=production
APP_PORT=8080
APP_HOST=0.0.0.0

# Optional: Vertex AI (for enterprise)
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_CLOUD_LOCATION=us-central1
```

### Step 4: Run the Application

```bash
# Development
python app.py

# Production (with Gunicorn on Linux)
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080

# Production (Windows)
uvicorn app:app --host 0.0.0.0 --port 8080 --workers 4
```

### Step 5: Access the Application

Open browser: `http://your-server-ip:8080`

---

## Configuration

### Agent Configuration

Edit `helpdesk_bot/agent.py` to customize:

```python
# Change the model (options: gemini-2.0-flash, gemini-1.5-pro)
model="gemini-2.0-flash"  # Fast, cost-effective
model="gemini-1.5-pro"    # More capable, higher cost

# Modify routing categories
ROUTER_INSTRUCTION = """
...
## Intent Categories
**HR** - Route to hr_agent for:
- [Add your organization's HR topics]

**IT_Support** - Route to it_support_agent for:
- [Add your organization's IT topics]
...
"""
```

### Sub-Agent Configuration

Each sub-agent can be customized in `helpdesk_bot/sub_agents/`:

| File | Purpose |
|------|---------|
| `hr_agent.py` | HR workflows, company policies |
| `it_support_agent.py` | IT support, software, hardware |
| `sales_agent.py` | Sales processes, CRM |
| `legal_agent.py` | Legal/compliance workflows |
| `off_topic_agent.py` | Handle non-work queries |

---

## Notification Integrations (Built-In)

The escalation system in `helpdesk_bot/tools/escalation_tools.py` includes **ready-to-use integrations** for:

### Microsoft Teams (Webhooks)

Notifications are sent as rich Adaptive Cards to Teams channels.

**Setup:**
1. Create Incoming Webhooks in Teams channels (see [SETUP_GUIDE.md](SETUP_GUIDE.md))
2. Configure in `.env`:
```env
ENABLE_NOTIFICATIONS=true
TEAMS_WEBHOOK_IT=https://yourcompany.webhook.office.com/...
TEAMS_WEBHOOK_HR=https://yourcompany.webhook.office.com/...
TEAMS_WEBHOOK_SALES=https://yourcompany.webhook.office.com/...
TEAMS_WEBHOOK_LEGAL=https://yourcompany.webhook.office.com/...
```

### Email (SMTP)

Direct email notifications to assigned specialists.

**Setup:**
```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=helpdesk@yourcompany.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=helpdesk@yourcompany.com
FROM_NAME=HelpDesk Bot
```

### ServiceNow (Auto-Ticketing)

Incidents are automatically created when users escalate.

**Setup:**
```env
SERVICENOW_ENABLED=true
SERVICENOW_INSTANCE=https://yourcompany.service-now.com
SERVICENOW_USERNAME=integration_user
SERVICENOW_PASSWORD=your_password
SNOW_GROUP_IT=IT Support
SNOW_GROUP_HR=Human Resources
```

**Available ServiceNow Functions:**
| Function | Purpose |
|----------|---------|
| `create_servicenow_incident()` | Create incident on escalation |
| `update_servicenow_incident()` | Update ticket fields |
| `get_servicenow_incident()` | Check ticket status |
| `add_servicenow_comment()` | Add comments/work notes |
| `close_servicenow_incident()` | Resolve tickets |

> 📖 **Full setup instructions:** See [SETUP_GUIDE.md](SETUP_GUIDE.md) for step-by-step configuration.

---

## Integrating with Additional Systems

### IT Systems Integration (ServiceNow - Advanced)

The built-in ServiceNow integration handles escalations. For IT-specific tickets, edit `helpdesk_bot/tools/it_tools.py`:

```python
import requests

# ServiceNow configuration
SERVICENOW_INSTANCE = "your-instance.service-now.com"
SERVICENOW_USER = os.getenv("SERVICENOW_USER")
SERVICENOW_PASS = os.getenv("SERVICENOW_PASS")

def create_support_ticket(
    employee_id: str,
    category: str,
    subject: str,
    description: str,
    priority: str = "medium"
) -> dict:
    """Create a real ServiceNow ticket."""
    
    # Map priority to ServiceNow values
    priority_map = {"low": 4, "medium": 3, "high": 2, "critical": 1}
    
    payload = {
        "caller_id": employee_id,
        "category": category,
        "short_description": subject,
        "description": description,
        "priority": priority_map.get(priority, 3)
    }
    
    response = requests.post(
        f"https://{SERVICENOW_INSTANCE}/api/now/table/incident",
        auth=(SERVICENOW_USER, SERVICENOW_PASS),
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        data = response.json()
        return {
            "status": "created",
            "ticket_id": data["result"]["number"],
            "sys_id": data["result"]["sys_id"],
            "message": f"Ticket {data['result']['number']} created successfully"
        }
    else:
        return {"status": "error", "message": response.text}
```

### HR Systems Integration (Workday)

Edit `helpdesk_bot/tools/hr_tools.py`:

```python
import requests

WORKDAY_TENANT = os.getenv("WORKDAY_TENANT")
WORKDAY_TOKEN = os.getenv("WORKDAY_TOKEN")

def check_pto_balance(employee_id: str) -> dict:
    """Get real PTO balance from Workday."""
    
    headers = {
        "Authorization": f"Bearer {WORKDAY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"https://{WORKDAY_TENANT}.workday.com/api/v1/workers/{employee_id}/timeOff",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        return {
            "employee_id": employee_id,
            "pto_balance": data["balance"],
            "as_of_date": data["asOfDate"]
        }
    else:
        return {"error": "Unable to fetch PTO balance"}
```

### CRM Integration (Salesforce)

Edit `helpdesk_bot/tools/sales_tools.py`:

```python
from simple_salesforce import Salesforce

def get_salesforce_client():
    return Salesforce(
        username=os.getenv("SF_USERNAME"),
        password=os.getenv("SF_PASSWORD"),
        security_token=os.getenv("SF_TOKEN")
    )

def lookup_customer(
    customer_id: str = None,
    company_name: str = None,
    email: str = None
) -> dict:
    """Look up customer in Salesforce."""
    
    sf = get_salesforce_client()
    
    if customer_id:
        query = f"SELECT Id, Name, Industry, Type FROM Account WHERE Id = '{customer_id}'"
    elif company_name:
        query = f"SELECT Id, Name, Industry, Type FROM Account WHERE Name LIKE '%{company_name}%'"
    elif email:
        query = f"SELECT Account.Id, Account.Name FROM Contact WHERE Email = '{email}'"
    else:
        return {"error": "Please provide search criteria"}
    
    results = sf.query(query)
    
    if results["totalSize"] > 0:
        return {"found": True, "customer": results["records"][0]}
    return {"found": False, "message": "Customer not found"}
```

---

## Customization

### Adding New Departments/Categories

1. **Create a new sub-agent** in `helpdesk_bot/sub_agents/`:

```python
# helpdesk_bot/sub_agents/facilities_agent.py

from google.adk.agents import Agent
from ..tools.facilities_tools import (
    book_meeting_room,
    report_maintenance_issue,
    request_parking,
)

FACILITIES_INSTRUCTION = """You are the Facilities Support Agent.

You handle:
- Meeting room bookings
- Maintenance requests
- Parking requests
- Office supplies
...
"""

facilities_agent = Agent(
    name="facilities_agent",
    model="gemini-2.0-flash",
    description="Handles facilities and office management requests",
    instruction=FACILITIES_INSTRUCTION,
    tools=[book_meeting_room, report_maintenance_issue, request_parking],
)
```

2. **Create tools** in `helpdesk_bot/tools/facilities_tools.py`

3. **Register the agent** in `helpdesk_bot/agent.py`:

```python
from .sub_agents.facilities_agent import facilities_agent

root_agent = Agent(
    name="helpdesk_router",
    ...
    sub_agents=[
        hr_agent,
        it_support_agent,
        sales_agent,
        legal_agent,
        facilities_agent,  # Add here
        off_topic_agent,
    ],
)
```

4. **Update router instructions** to include new category

### Customizing the UI

Edit files in `static/` folder:

| File | Purpose |
|------|---------|
| `static/index.html` | Main HTML structure |
| `static/css/styles.css` | Styling, colors, branding |
| `static/js/app.js` | Chat functionality |

**Branding Example:**
```css
/* static/css/styles.css */
:root {
    --primary-color: #YOUR_BRAND_COLOR;
    --primary-hover: #YOUR_HOVER_COLOR;
}

.logo span {
    content: "Your Company HelpDesk";
}
```

---

## Deployment Options

### Option 1: Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  helpdesk-bot:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

### Option 2: Cloud Run (Google Cloud)

```bash
# Build and deploy
gcloud run deploy helpdesk-bot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY
```

### Option 3: Azure App Service

```bash
# Create App Service
az webapp create \
  --name helpdesk-bot \
  --resource-group your-rg \
  --plan your-plan \
  --runtime "PYTHON:3.11"

# Configure
az webapp config appsettings set \
  --name helpdesk-bot \
  --settings GOOGLE_API_KEY=$GOOGLE_API_KEY

# Deploy
az webapp up --name helpdesk-bot
```

### Option 4: AWS (Elastic Beanstalk)

Create `.ebextensions/python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
  aws:elasticbeanstalk:application:environment:
    GOOGLE_API_KEY: your_key
```

Deploy:
```bash
eb init -p python-3.11 helpdesk-bot
eb create production
```

---

## Security Considerations

### API Key Security

```python
# Never hardcode keys
# BAD:
GOOGLE_API_KEY = "AIzaSy..."

# GOOD:
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
```

### Authentication (Add to app.py)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from your identity provider."""
    token = credentials.credentials
    
    # Integrate with your SSO (Azure AD, Okta, etc.)
    # Example with Azure AD:
    try:
        # Verify token with your identity provider
        user = verify_azure_ad_token(token)
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )

# Protect endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, user: dict = Depends(verify_token)):
    # user is now authenticated
    ...
```

### Data Privacy

1. **Don't log sensitive data:**
```python
# Mask employee IDs in logs
logger.info(f"Request from employee: {employee_id[:4]}****")
```

2. **Session expiry:**
```python
# Add to app.py
SESSION_EXPIRY_HOURS = 8

async def cleanup_expired_sessions():
    current_time = datetime.now()
    expired = [
        sid for sid, data in sessions.items()
        if (current_time - data["created_at"]).hours > SESSION_EXPIRY_HOURS
    ]
    for sid in expired:
        del sessions[sid]
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/chat")
@limiter.limit("30/minute")
async def chat(request: Request, message: ChatMessage):
    ...
```

---

## Monitoring & Maintenance

### Health Check Endpoint

Already included at `/api/health`:
```bash
curl http://your-server:8080/api/health
# {"status":"healthy","agent":"helpdesk_bot"}
```

### Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('helpdesk_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Metrics to Track

| Metric | Purpose |
|--------|---------|
| Request count per agent | Understand usage patterns |
| Response time | Performance monitoring |
| Error rate | Reliability tracking |
| Routing accuracy | Agent effectiveness |

### Backup & Recovery

```bash
# Backup configuration
tar -czvf helpdesk-backup.tar.gz \
  .env \
  helpdesk_bot/ \
  static/

# Store in secure location
aws s3 cp helpdesk-backup.tar.gz s3://your-backup-bucket/
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `GOOGLE_API_KEY not set` | Check `.env` file exists and is loaded |
| `500 Internal Server Error` | Check terminal logs for detailed error |
| `Connection refused` | Ensure app is running on correct port |
| `CORS errors` | Add frontend origin to CORS settings |
| `Rate limit exceeded` | Upgrade API plan or implement caching |

### Debug Mode

```python
# Run with debug logging
import logging
logging.getLogger("google.adk").setLevel(logging.DEBUG)
```

### Test Individual Components

```python
# test_tools.py
from helpdesk_bot.tools.it_tools import diagnose_hardware_issue

result = diagnose_hardware_issue(
    employee_id="EMP001",
    device_type="laptop",
    issue_description="My laptop is very slow",
    symptoms="slow, freezing"
)
print(result)
```

---

## Support & Resources

- **Setup Guide (Start Here):** [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Enterprise Deployment:** [ENTERPRISE_DEPLOYMENT.md](ENTERPRISE_DEPLOYMENT.md)
- **Google ADK Documentation:** https://google.github.io/adk-docs/
- **Gemini API Reference:** https://ai.google.dev/docs
- **FastAPI Documentation:** https://fastapi.tiangolo.com/

---

## Appendix: Environment Variables Reference

### Core Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google AI Studio API key |
| `APP_PORT` | No | Server port (default: 8080) |
| `APP_HOST` | No | Server host (default: 0.0.0.0) |
| `REQUIRE_AUTH` | No | Enable authentication (default: false) |
| `AUTH_METHOD` | No | basic, ldap, sso, oauth_google, oauth_microsoft |

### Notification Settings

| Variable | Required | Description |
|----------|----------|-------------|
| `ENABLE_NOTIFICATIONS` | No | Enable Teams/Email notifications (default: false) |
| `TEAMS_WEBHOOK_IT` | No | Teams webhook URL for IT channel |
| `TEAMS_WEBHOOK_HR` | No | Teams webhook URL for HR channel |
| `TEAMS_WEBHOOK_SALES` | No | Teams webhook URL for Sales channel |
| `TEAMS_WEBHOOK_LEGAL` | No | Teams webhook URL for Legal channel |

### Email Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `SMTP_SERVER` | No | SMTP server (smtp.office365.com) |
| `SMTP_PORT` | No | SMTP port (default: 587) |
| `SMTP_USERNAME` | No | SMTP login username |
| `SMTP_PASSWORD` | No | SMTP password or app password |
| `FROM_EMAIL` | No | Sender email address |
| `FROM_NAME` | No | Sender display name |

### ServiceNow Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `SERVICENOW_ENABLED` | No | Enable ServiceNow integration (default: false) |
| `SERVICENOW_INSTANCE` | No | ServiceNow instance URL |
| `SERVICENOW_USERNAME` | No | ServiceNow API user |
| `SERVICENOW_PASSWORD` | No | ServiceNow API password |
| `SERVICENOW_API_KEY` | No | Alternative: OAuth token |
| `SNOW_GROUP_IT` | No | IT assignment group name |
| `SNOW_GROUP_HR` | No | HR assignment group name |
| `SNOW_GROUP_SALES` | No | Sales assignment group name |
| `SNOW_GROUP_LEGAL` | No | Legal assignment group name |

### External Systems (Optional)

| Variable | Required | Description |
|----------|----------|-------------|
| `WORKDAY_TENANT` | No | Workday tenant ID |
| `WORKDAY_TOKEN` | No | Workday API token |
| `SF_USERNAME` | No | Salesforce username |
| `SF_PASSWORD` | No | Salesforce password |
| `SF_TOKEN` | No | Salesforce security token |

---

**Version:** 1.1  
**Last Updated:** February 2026
