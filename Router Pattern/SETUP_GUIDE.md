# HelpDesk Bot - Setup Guide

A complete step-by-step guide to set up and test the HelpDesk Bot with Google ADK, Microsoft Teams, Email, and ServiceNow integrations.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Google AI API Setup](#3-google-ai-api-setup)
4. [Basic Configuration](#4-basic-configuration)
5. [Run & Test (Basic Mode)](#5-run--test-basic-mode)
6. [Microsoft Teams Integration](#6-microsoft-teams-integration)
7. [Email Notification Setup](#7-email-notification-setup)
8. [ServiceNow Integration](#8-servicenow-integration)
9. [Specialist Data Sources](#9-specialist-data-sources)
10. [Enable All Notifications](#10-enable-all-notifications)
11. [Testing the Full Integration](#11-testing-the-full-integration)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

### Required Software

| Software | Version | Download |
|----------|---------|----------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| pip | Latest | Comes with Python |
| Git | Any | [git-scm.com](https://git-scm.com/) |

### Required Accounts

| Account | Purpose | Sign Up |
|---------|---------|---------|
| Google AI Studio | Gemini API Key | [aistudio.google.com](https://aistudio.google.com/) |
| Microsoft 365 (optional) | Teams & Email | Your organization |
| ServiceNow (optional) | Ticket creation | Your organization |

---

## 2. Installation

### Step 2.1: Clone/Download the Project

```bash
# If using git
git clone <your-repo-url>
cd "Router Pattern"

# Or just navigate to the project folder
cd "C:\Users\Harsha Kumar\Desktop\DRAVYN\Agents\Router Pattern"
```

### Step 2.2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment (Windows - use full Python path if issues occur)
python -m venv venv

# If the above creates an incomplete venv (missing activate.bat), use:
# C:\Python313\python.exe -m venv venv

# Activate it (Windows CMD)
venv\Scripts\activate.bat

# Activate it (Windows PowerShell)
venv\Scripts\Activate.ps1

# Activate it (Mac/Linux)
source venv/bin/activate
```

### Step 2.3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed google-adk-0.3.0 google-generativeai-0.5.0 ...
```

### Step 2.4: Create Environment File

```bash
# Copy the example file
copy .env.example .env

# Or on Mac/Linux
cp .env.example .env
```

---

## 3. Google AI API Setup

### Step 3.1: Get API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **"Get API Key"** in the left sidebar
4. Click **"Create API Key"**
5. Copy the generated key

### Step 3.2: Add to .env File

Open `.env` and add your key:

```env
GOOGLE_API_KEY=AIzaSy...your_key_here
```

### Step 3.3: Verify API Key

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key set:', bool(os.getenv('GOOGLE_API_KEY')))"
```

**Expected output:** `API Key set: True`

---

## 4. Basic Configuration

Your `.env` file should have at minimum:

```env
# ============================================================
# REQUIRED - Google AI
# ============================================================
GOOGLE_API_KEY=your_google_api_key_here

# ============================================================
# REQUIRED - Application Base URL (for specialist chat links)
# ============================================================
# This is the URL where your application is hosted
# Specialists will receive this URL to join user chat sessions
APP_BASE_URL=http://localhost:8000

# For production, use your actual domain:
# APP_BASE_URL=https://helpdesk.yourcompany.com

# ============================================================
# OPTIONAL - Authentication (set to false for testing)
# ============================================================
REQUIRE_AUTH=false

# ============================================================
# OPTIONAL - Notifications (enable later)
# ============================================================
ENABLE_NOTIFICATIONS=false
SERVICENOW_ENABLED=false
```

---

## 5. Run & Test (Basic Mode)

### Option A: Run with Python

```bash
python main.py
```

**Expected output:**
```
╔════════════════════════════════════════════╗
║         HelpDesk Bot - Interactive         ║
╚════════════════════════════════════════════╝

Type your message and press Enter.
Type 'quit' or 'exit' to end the session.
Type 'clear' to start a new conversation.

You: 
```

### Option B: Run with Google ADK CLI

```bash
adk run helpdesk_bot
```

### Option C: Run with Web UI

```bash
adk web
```
Then open http://localhost:8000 in your browser.

### Option D: Run FastAPI Server

```bash
python app.py
```
Then open http://localhost:8000 in your browser.

---

## 🧪 Test Prompts (Basic Mode)

Try these messages to test each agent:

| Test Message | Expected Routing |
|--------------|------------------|
| `My laptop is slow` | IT Support Agent |
| `I need Adobe license` | IT Support Agent |
| `Request PTO for next week` | HR Agent |
| `What's our health insurance?` | HR Agent |
| `Customer wants a quote` | Sales Agent |
| `Review this contract` | Legal Agent |
| `What's the weather today?` | Off-Topic Agent |
| `My laptop is slow AND I need PTO` | Multiple agents |

---

## 6. Microsoft Teams Integration

### Step 6.1: Create Incoming Webhooks

For **each department** (IT, HR, Sales, Legal), create a webhook:

1. Open **Microsoft Teams**
2. Go to the target channel (e.g., "IT Support")
3. Click the **⋯** (three dots) next to the channel name
4. Select **"Connectors"** (or "Manage channel" → "Connectors")
5. Find **"Incoming Webhook"** and click **"Configure"**
6. Name it: `HelpDesk Bot`
7. Optionally add an icon
8. Click **"Create"**
9. **Copy the webhook URL** (it looks like: `https://yourcompany.webhook.office.com/webhookb2/...`)
10. Click **"Done"**

### Step 6.2: Add Webhooks to .env

```env
# Microsoft Teams Webhooks
TEAMS_WEBHOOK_IT=https://yourcompany.webhook.office.com/webhookb2/xxx/IncomingWebhook/xxx
TEAMS_WEBHOOK_HR=https://yourcompany.webhook.office.com/webhookb2/xxx/IncomingWebhook/xxx
TEAMS_WEBHOOK_SALES=https://yourcompany.webhook.office.com/webhookb2/xxx/IncomingWebhook/xxx
TEAMS_WEBHOOK_LEGAL=https://yourcompany.webhook.office.com/webhookb2/xxx/IncomingWebhook/xxx
```

### Step 6.3: Test Teams Webhook

```python
# Quick test script - save as test_teams.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

webhook_url = os.getenv("TEAMS_WEBHOOK_IT")
if webhook_url:
    response = requests.post(
        webhook_url,
        json={"text": "🧪 Test message from HelpDesk Bot!"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print("Check your Teams channel!")
else:
    print("TEAMS_WEBHOOK_IT not set in .env")
```

Run: `python test_teams.py`

---

## 7. Email Notification Setup

### Option A: Microsoft 365 (Recommended)

#### Step 7.1: Get App Password

1. Go to [account.microsoft.com/security](https://account.microsoft.com/security)
2. Click **"Advanced security options"**
3. Under "App passwords", click **"Create a new app password"**
4. Copy the generated password

#### Step 7.2: Configure .env

```env
# Email Configuration (Microsoft 365)
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yourcompany.com
SMTP_PASSWORD=your_app_password_here
FROM_EMAIL=helpdesk@yourcompany.com
FROM_NAME=HelpDesk Bot
```

### Option B: Gmail

#### Step 7.1: Enable 2FA and Create App Password

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled
3. Go to **App passwords**
4. Select "Mail" and "Windows Computer"
5. Click **Generate**
6. Copy the 16-character password

#### Step 7.2: Configure .env

```env
# Email Configuration (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=HelpDesk Bot
```

### Step 7.3: Test Email

```python
# Quick test script - save as test_email.py
import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

msg = MIMEText("🧪 Test email from HelpDesk Bot!")
msg["Subject"] = "HelpDesk Bot - Test"
msg["From"] = os.getenv("FROM_EMAIL")
msg["To"] = "your-test-email@example.com"  # Change this!

try:
    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
        server.send_message(msg)
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
```

Run: `python test_email.py`

---

## 8. ServiceNow Integration

### Step 8.1: Create Integration User in ServiceNow

1. Log into ServiceNow as admin
2. Go to **User Administration → Users**
3. Click **New**
4. Fill in:
   - User ID: `helpdesk_bot`
   - First name: `HelpDesk`
   - Last name: `Bot Integration`
   - Email: `helpdesk-integration@yourcompany.com`
   - Password: (generate a strong password)
5. **Save**

### Step 8.2: Assign Roles

1. Open the user you just created
2. Scroll to **Roles** tab
3. Click **Edit**
4. Add these roles:
   - `itil` (allows incident creation)
   - `rest_api_user` (allows API access)
5. **Save**

### Step 8.3: Verify REST API is Enabled

1. Go to **System Web Services → REST API Explorer**
2. If it loads, REST API is enabled
3. If not, contact your ServiceNow admin

### Step 8.4: Get Assignment Group sys_ids (Optional)

1. Go to **User Administration → Groups**
2. Find each group (IT Support, HR, etc.)
3. Note the **Name** exactly as shown (case-sensitive)

### Step 8.5: Configure .env

```env
# ServiceNow Integration
SERVICENOW_ENABLED=true
SERVICENOW_INSTANCE=https://yourcompany.service-now.com
SERVICENOW_USERNAME=helpdesk_bot
SERVICENOW_PASSWORD=your_integration_password

# Assignment Groups (must match exactly)
SNOW_GROUP_IT=IT Support
SNOW_GROUP_HR=Human Resources
SNOW_GROUP_SALES=Sales Operations
SNOW_GROUP_LEGAL=Legal
```

### Step 8.6: Test ServiceNow Connection

```python
# Quick test script - save as test_servicenow.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

instance = os.getenv("SERVICENOW_INSTANCE")
username = os.getenv("SERVICENOW_USERNAME")
password = os.getenv("SERVICENOW_PASSWORD")

if not all([instance, username, password]):
    print("❌ ServiceNow credentials not configured")
    exit()

# Test API connection
url = f"{instance}/api/now/table/incident?sysparm_limit=1"
response = requests.get(
    url,
    auth=(username, password),
    headers={"Accept": "application/json"}
)

if response.status_code == 200:
    print("✅ ServiceNow connection successful!")
    print(f"   Instance: {instance}")
elif response.status_code == 401:
    print("❌ Authentication failed - check username/password")
else:
    print(f"❌ Error: {response.status_code} - {response.text[:200]}")
```

Run: `python test_servicenow.py`

---

## 9. Specialist Data Sources

Configure where specialist/expert data is loaded from. The bot supports multiple data sources.

### Option A: CSV File (Recommended for simplicity)

**Step 9.1:** Edit `data/specialists.csv`:

```csv
department,name,email,expertise,available,phone
IT_Support,Alex Chen,alex.chen@company.com,"hardware,network,security",true,+1-555-0101
IT_Support,Maria Garcia,maria.garcia@company.com,"software,licenses,cloud",true,+1-555-0102
HR,Sarah Johnson,sarah.johnson@company.com,"benefits,payroll,leave",true,+1-555-0201
```

**Step 9.2:** Update `.env`:

```env
SPECIALIST_SOURCE=csv
SPECIALISTS_CSV_PATH=data/specialists.csv
```

### Option B: JSON File

**Step 9.1:** Edit `data/specialists.json`:

```json
{
  "IT_Support": [
    {"name": "Alex Chen", "email": "alex.chen@company.com", "expertise": ["hardware"], "available": true}
  ],
  "HR": [...]
}
```

**Step 9.2:** Update `.env`:

```env
SPECIALIST_SOURCE=json
SPECIALISTS_JSON_PATH=data/specialists.json
```

### Option C: SQLite Database

**Step 9.1:** Create the database and table:

```sql
-- Create table
CREATE TABLE specialists (
    id INTEGER PRIMARY KEY,
    department VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    expertise TEXT,
    available BOOLEAN DEFAULT TRUE,
    phone VARCHAR(20),
    active BOOLEAN DEFAULT TRUE
);

-- Insert data
INSERT INTO specialists (department, name, email, expertise, available)
VALUES ('IT_Support', 'Alex Chen', 'alex.chen@company.com', 'hardware,network', 1);
```

**Step 9.2:** Update `.env`:

```env
SPECIALIST_SOURCE=database
SPECIALISTS_DB_TYPE=sqlite
SPECIALISTS_DB_CONNECTION=data/specialists.db
```

### Option D: PostgreSQL Database

```env
SPECIALIST_SOURCE=database
SPECIALISTS_DB_TYPE=postgresql
SPECIALISTS_DB_CONNECTION=postgresql://user:password@localhost:5432/helpdesk
```

Install required package: `pip install psycopg2-binary`

### Option E: ServiceNow (Load from assignment groups)

Loads specialists from ServiceNow `sys_user_group` membership:

```env
SPECIALIST_SOURCE=servicenow
# ServiceNow must be configured (see Section 8)
```

### Option F: Active Directory / LDAP

Loads specialists from AD group membership:

**Step 9.1:** Install LDAP library:

```bash
pip install ldap3
```

**Step 9.2:** Update `.env`:

```env
SPECIALIST_SOURCE=ldap
LDAP_SERVER=ldap://ldap.company.com:389
LDAP_USE_SSL=true
LDAP_BASE_DN=dc=company,dc=com
LDAP_BIND_DN=cn=service,dc=company,dc=com
LDAP_BIND_PASSWORD=service_password

# Map AD groups to departments
AD_GROUP_IT=CN=IT Support,OU=Groups
AD_GROUP_HR=CN=Human Resources,OU=Groups
AD_GROUP_SALES=CN=Sales Team,OU=Groups
AD_GROUP_LEGAL=CN=Legal Department,OU=Groups
```

### Cache Settings

Specialist data is cached to avoid repeated API/database calls:

```env
# Cache duration in minutes (default: 15)
SPECIALISTS_CACHE_TTL=15
```

### Test Specialist Loading

```bash
# Test your configured source
python helpdesk_bot/tools/specialist_loader.py

# Or test a specific source
python helpdesk_bot/tools/specialist_loader.py csv
python helpdesk_bot/tools/specialist_loader.py json
python helpdesk_bot/tools/specialist_loader.py database
```

---

## 10. Enable All Notifications

Once all integrations are tested individually, enable them:

```env
# Enable real notifications
ENABLE_NOTIFICATIONS=true
SERVICENOW_ENABLED=true
```

---

## 11. Testing the Full Integration

### Step 11.1: Start the Bot

```bash
python main.py
# or
python app.py
```

### Step 11.2: Test Escalation Flow

Type this message:

```
I have a critical laptop issue that needs human help
```

The bot should:
1. Route to IT Support Agent
2. Offer escalation option
3. When escalated:
   - ✅ Create ServiceNow incident (INC...)
   - ✅ Send Teams notification to IT channel
   - ✅ Send email to assigned specialist

### Step 11.3: Verify Results

| Check | Where to Look |
|-------|---------------|
| ServiceNow Ticket | ServiceNow → Incidents → Search for correlation_id |
| Teams Message | IT Support Teams channel |
| Email | Assigned specialist's inbox |

### Step 11.4: Test Message Examples

```
# IT Support escalation
"My laptop crashed and I've lost all my files. This is urgent!"

# HR escalation
"I need to discuss a sensitive HR matter with someone"

# Multi-intent
"I need my laptop fixed AND I want to request PTO"
```

---

## 12. Troubleshooting

### Common Issues

#### ❌ Windows: "venv\Scripts\activate" not recognized

**Symptoms:** The venv folder is created but missing `activate.bat` and other scripts.

**Solution:** Your Python installation may be creating incomplete venvs. Use the full path to Python:
```bash
# Remove incomplete venv
rmdir /s /q venv

# Create venv using full Python path (adjust path to your Python installation)
C:\Python313\python.exe -m venv venv

# Verify activate.bat exists
dir venv\Scripts\*.bat

# Activate
venv\Scripts\activate.bat
```

If multiple Python versions are installed, run `where python` to find the correct path.

#### ❌ "GOOGLE_API_KEY environment variable not set"

**Solution:** Make sure your `.env` file exists and has the key:
```bash
# Check if file exists
dir .env  # Windows
ls -la .env  # Mac/Linux

# Verify content
type .env  # Windows
cat .env  # Mac/Linux
```

#### ❌ "ModuleNotFoundError: No module named 'google.adk'"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

#### ❌ Teams webhook returns 400 error

**Solution:** Verify webhook URL is complete and not expired. Create a new webhook if needed.

#### ❌ Email authentication failed

**Solution:** 
- For Microsoft 365: Use app password, not regular password
- For Gmail: Enable 2FA first, then create app password
- Check SMTP_USERNAME matches FROM_EMAIL

#### ❌ ServiceNow 401 Unauthorized

**Solution:**
- Verify username/password are correct
- Ensure user has `rest_api_user` role
- Check if account is locked

#### ❌ ServiceNow "Assignment group not found"

**Solution:** Group names must match exactly (case-sensitive). Check your ServiceNow group names.

---

## Quick Reference - Environment Variables

```env
# ============ REQUIRED ============
GOOGLE_API_KEY=your_google_api_key

# ============ NOTIFICATIONS ============
ENABLE_NOTIFICATIONS=true

# ============ TEAMS ============
TEAMS_WEBHOOK_IT=https://...
TEAMS_WEBHOOK_HR=https://...
TEAMS_WEBHOOK_SALES=https://...
TEAMS_WEBHOOK_LEGAL=https://...

# ============ EMAIL ============
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=helpdesk@company.com
SMTP_PASSWORD=app_password_here
FROM_EMAIL=helpdesk@company.com
FROM_NAME=HelpDesk Bot

# ============ SERVICENOW ============
SERVICENOW_ENABLED=true
SERVICENOW_INSTANCE=https://company.service-now.com
SERVICENOW_USERNAME=integration_user
SERVICENOW_PASSWORD=password
SNOW_GROUP_IT=IT Support
SNOW_GROUP_HR=Human Resources
SNOW_GROUP_SALES=Sales Operations
SNOW_GROUP_LEGAL=Legal
```

---

## Next Steps

Once everything is working:

1. **Customize specialists** - Update `SPECIALISTS` dict in `escalation_tools.py` with real people
2. **Adjust categories** - Modify `SERVICENOW_CATEGORIES` to match your ServiceNow setup
3. **Add authentication** - Set `REQUIRE_AUTH=true` and configure SSO/LDAP
4. **Deploy** - See `DEPLOYMENT_GUIDE.md` for production deployment

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs in the terminal
3. Test each integration individually before enabling all

Happy testing! 🚀
