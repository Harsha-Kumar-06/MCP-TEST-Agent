# 🤖 HelpDesk Bot - AI-Powered Internal Support Agent

An intelligent Gateway agent built with **Google ADK** that classifies user intent and routes requests to specialized AI agents. Perfect for enterprise internal support.

---

## 📋 Table of Contents

- [What is HelpDesk Bot?](#what-is-helpdesk-bot)
- [Features](#features)
- [Quick Start](#quick-start)
- [Running the Agent](#running-the-agent)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Customization](#customization)
- [Enterprise Deployment](#enterprise-deployment)

---

## What is HelpDesk Bot?

HelpDesk Bot is an **AI-powered internal support system** that acts as the first line of defense for employee queries. Instead of a single chatbot trying to handle everything, it uses a **Router Pattern** to intelligently route requests to specialized agents.

### The Problem It Solves

❌ Traditional chatbots → One-size-fits-all, poor at specialized tasks  
✅ HelpDesk Bot → Routes to expert agents for HR, IT, Sales, Legal

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
│              "My laptop is slow and I need PTO info"            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   🎯 HELPDESK ROUTER                             │
│                   (Gemini 2.0 Flash)                            │
│                                                                  │
│   Analyzes intent → Classifies category → Routes to expert      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   👥 HR       │   │   💻 IT       │   │   💰 Sales    │
│   Agent       │   │   Support     │   │   Agent       │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ • PTO         │   │ • Hardware    │   │ • Quotes      │
│ • Benefits    │   │ • Software    │   │ • Pricing     │
│ • Payroll     │   │ • Access      │   │ • CRM         │
│ • Policies    │   │ • Passwords   │   │ • Customers   │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐
│   ⚖️ Legal    │   │   🚫 Off-     │
│   Agent       │   │   Topic       │
├───────────────┤   ├───────────────┤
│ • Contracts   │   │ • Redirects   │
│ • Compliance  │   │ • Friendly    │
│ • NDAs        │   │   decline     │
│ • Templates   │   │               │
└───────────────┘   └───────────────┘
```

---

## Features

### Core Features

| Feature | Description |
|---------|-------------|
| 🎯 **Smart Routing** | Automatically classifies and routes to the right agent |
| 🔍 **Knowledge Base Search** | RAG-powered search using ChromaDB + Gemini embeddings |
| 👤 **Human Escalation** | Route to real specialists when AI can't help |
| 💬 **Live Chat** | Connect users to human agents |
| 📞 **Callback Scheduling** | Schedule calls with specialists |
| 🔐 **Authentication** | SSO, LDAP, OAuth support for enterprise |
| 📝 **Audit Logging** | Track all interactions for compliance |

### Notification Integrations (NEW)

| Integration | Description |
|-------------|-------------|
| 📢 **Microsoft Teams** | Send Adaptive Cards to Teams channels via webhooks |
| 📧 **Email Notifications** | SMTP email alerts to specialists (M365, Gmail) |
| 🎫 **ServiceNow** | Auto-create incidents/tickets on escalation |
| 🔔 **Multi-Channel Alerts** | Notify via Teams + Email + ServiceNow simultaneously |

### Specialized Agents

| Agent | Handles |
|-------|---------|
| **HR Agent** | PTO requests, benefits info, payroll questions, company policies |
| **IT Support** | Hardware issues, software licenses, password resets, VPN setup |
| **Sales Agent** | Customer lookups, quotes, pricing, CRM updates |
| **Legal Agent** | Contract review, compliance checks, NDAs, legal templates |
| **Off-Topic Handler** | Politely redirects non-work queries |

---

## Quick Start

> 📖 **For detailed step-by-step instructions**, see [SETUP_GUIDE.md](SETUP_GUIDE.md)

### Prerequisites

- Python 3.10+
- Google AI API Key ([Get one here](https://aistudio.google.com/apikey))

### Installation

```bash
# 1. Navigate to the project
cd "Router Pattern"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
copy .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Get Your API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click "Create API Key"
3. Copy the key and paste it in your `.env` file:
   ```
   GOOGLE_API_KEY=AIzaSy...your_key_here
   ```

---

## Running the Agent

### Option 1: Custom Web UI (Recommended) ⭐

```bash
python app.py
```

**Open:** http://localhost:8080

Features:
- Professional chat interface
- Dark/light theme toggle
- Quick action buttons
- Real-time responses

### Option 2: ADK Web Interface

```bash
adk web
```

**Open:** http://localhost:8000

### Option 3: Command Line

```bash
adk run helpdesk_bot
```

### Option 4: Python Script

```python
from helpdesk_bot import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

runner = Runner(
    agent=root_agent,
    app_name="helpdesk_bot",
    session_service=InMemorySessionService(),
)

# Send a message
async for event in runner.run_async(
    session_id="test",
    user_id="user1",
    new_message="How do I reset my password?"
):
    print(event)
```

---

## Project Structure

```
Router Pattern/
├── 📁 helpdesk_bot/           # Main agent package
│   ├── __init__.py            # Package exports
│   ├── agent.py               # Router agent definition
│   │
│   ├── 📁 sub_agents/         # Specialized agents
│   │   ├── hr_agent.py        # HR specialist
│   │   ├── it_support_agent.py # IT support
│   │   ├── sales_agent.py     # Sales operations
│   │   ├── legal_agent.py     # Legal & compliance
│   │   └── off_topic_agent.py # Off-topic handler
│   │
│   └── 📁 tools/              # Agent tools/functions
│       ├── hr_tools.py        # PTO, benefits, payroll
│       ├── it_tools.py        # Diagnostics, tickets
│       ├── sales_tools.py     # CRM, quotes, pricing
│       ├── legal_tools.py     # Contracts, compliance
│       ├── kb_tools.py        # Knowledge base (RAG)
│       └── escalation_tools.py # Human escalation + Teams/Email/ServiceNow
│
├── 📁 static/                 # Custom web UI
│   ├── index.html             # Chat interface
│   ├── css/styles.css         # Styling
│   └── js/app.js              # Frontend logic
│
├── app.py                     # FastAPI web server
├── auth.py                    # Authentication module
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── .env                       # Your configuration
├── SETUP_GUIDE.md             # ⭐ Step-by-step setup guide
├── DEPLOYMENT_GUIDE.md        # Deployment & customization
├── ENTERPRISE_DEPLOYMENT.md   # Auth, SSO, security
└── README.md                  # This file
```

---

## How It Works

### 1. User Sends Message

```
"My laptop is running slow and I need to check my PTO balance"
```

### 2. Router Analyzes Intent

The router agent uses Gemini to classify the request:
- Intent 1: IT Support (slow laptop)
- Intent 2: HR (PTO balance)

### 3. Routes to Specialists

**IT Support Agent:**
- Searches KB for "slow laptop" solutions
- Offers diagnostics or ticket creation

**HR Agent:**
- Calls `check_pto_balance` tool
- Returns PTO information

### 4. Unified Response

User receives a comprehensive response addressing all their needs.

---

## Example Conversations

### IT Support

```
User: My laptop is running slow

Agent: I found a KB article that might help!

**Slow Laptop Troubleshooting:**
1. Restart your laptop
2. Check disk space (should have >10GB free)
3. Close unnecessary browser tabs
4. Run Windows Disk Cleanup

If these don't help, I can create a support ticket or connect you 
with an IT specialist. Would you like me to do that?
```

### HR Query

```
User: What's my PTO balance?

Agent: Let me check your PTO balance.

📊 **Your PTO Balance:**
- Available: 15 days
- Used this year: 5 days
- Pending requests: 0 days

Would you like to submit a new PTO request?
```

### Human Escalation

```
User: I need to talk to someone about a complaint

Agent: I understand this is a sensitive matter. Let me connect you 
with an HR specialist who can help.

🔄 **Escalation Created:**
- Escalation ID: ESC-20260211143022
- ServiceNow Ticket: INC0012345
- Priority: High
- Department: HR
- Assigned To: Sarah Johnson

✅ Notifications sent:
- Teams: Message posted to HR channel
- Email: Sent to sarah.johnson@company.com
- ServiceNow: Incident INC0012345 created

Sarah will contact you within 15-30 minutes.
```

---

## Customization

### Adding a New Agent

1. Create agent file in `helpdesk_bot/sub_agents/`:

```python
# finance_agent.py
from google.adk.agents import Agent

finance_agent = Agent(
    name="finance_agent",
    model="gemini-2.0-flash",
    description="Finance specialist for expenses and budgets",
    instruction="You handle finance requests...",
    tools=[submit_expense, check_budget],
)
```

2. Register in `helpdesk_bot/agent.py`:

```python
from .sub_agents.finance_agent import finance_agent

root_agent = Agent(
    ...
    sub_agents=[hr_agent, it_support_agent, finance_agent, ...],
)
```

### Adding KB Articles

Edit `helpdesk_bot/tools/kb_tools.py`:

```python
SAMPLE_KB_ARTICLES.append({
    "id": "KB009",
    "title": "How to Submit Expense Reports",
    "category": "Finance",
    "content": "Step 1: Go to expense portal...",
    "keywords": ["expense", "reimbursement"],
})
```

---

## Enterprise Deployment

See [ENTERPRISE_DEPLOYMENT.md](ENTERPRISE_DEPLOYMENT.md) for full guide.

### Quick Auth Setup

```bash
# .env
REQUIRE_AUTH=true
AUTH_METHOD=basic
```

Demo credentials:
| Email | Password |
|-------|----------|
| john.doe@company.com | demo123 |
| admin@company.com | admin123 |

### Auth Options

- **Basic** - Email/password
- **LDAP** - Active Directory
- **SSO** - Okta, Azure AD
- **OAuth** - Google, Microsoft 365

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/chat` | POST | Send message |
| `/api/session/new` | POST | New session |
| `/api/health` | GET | Health check |
| `/api/auth/login` | POST | Login |

### Example Request

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "GOOGLE_API_KEY not set" | Add key to `.env` file |
| "Module not found" | Run `pip install -r requirements.txt` |
| Port 8080 in use | Change port in `app.py` or kill existing process |

---

## Documentation

| Document | Description |
|----------|-------------|
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | **Start here!** Step-by-step setup & testing guide |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Organization deployment & customization |
| [ENTERPRISE_DEPLOYMENT.md](ENTERPRISE_DEPLOYMENT.md) | Authentication, SSO, security hardening |

---

## License

MIT License - Free to use and modify.

---

## Links

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Get API Key](https://aistudio.google.com/apikey)
- [Setup Guide](SETUP_GUIDE.md)
- [Enterprise Deployment Guide](ENTERPRISE_DEPLOYMENT.md)
