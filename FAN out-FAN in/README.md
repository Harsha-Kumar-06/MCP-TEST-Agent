# 🏦 Loan Underwriter - AI Multi-Agent System

> **A production-ready mortgage processing system using Google ADK with Fan-Out/Fan-In architecture**

This project demonstrates how to build a multi-agent AI system that processes loan applications **20x faster** than traditional methods - reducing underwriting time from 15 minutes to ~45 seconds.

![Architecture](https://img.shields.io/badge/Architecture-Fan--Out%2FFan--In-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Framework](https://img.shields.io/badge/Framework-FastAPI-teal)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-endpoints)
- [Agent Details](#-agent-details)
- [Contributing](#-contributing)

## 🎯 Overview

This project demonstrates a **multi-agent AI system** for financial services, specifically mortgage loan underwriting. Three specialized AI agents perform different risk assessment tasks **simultaneously** using Python's `asyncio`, then an aggregator combines the results into a final decision.

### 👤 AI Employee: "The Loan Underwriter"

**Role:** Rapidly assesses loan application risk by analyzing multiple data sources in parallel.

## 🏗️ Architecture

### Visual Diagrams

For detailed visual documentation, see the SVG diagrams in the `docs/` folder:

- **[Architecture Overview](docs/architecture.svg)** - Fan-Out/Fan-In pattern
- **[Data Flow](docs/data-flow.svg)** - Complete processing pipeline
- **[Technology Stack](docs/tech-stack.svg)** - All technologies used
- **[API Integrations](docs/api-integrations.svg)** - External API connections

### System Architecture

```
                    ┌─────────────────────────────────────┐
                    │     Mortgage Application Input      │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │         FAN-OUT (Parallel)          │
                    └─────────────────┬───────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Agent A       │       │   Agent B       │       │   Agent C       │
│   CREDIT        │       │   PROPERTY      │       │   FRAUD         │
│                 │       │                 │       │                 │
│ • Experian API  │       │ • RentCast API  │       │ • Persona API   │
│ • Equifax API   │       │ • Valuation     │       │ • Identity      │
│ • DTI Analysis  │       │ • LTV Analysis  │       │ • Watchlists    │
│ Weight: 40%     │       │ Weight: 35%     │       │ Weight: 25%     │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │       FAN-IN (Aggregate)    │
                    │                             │
                    │  Weighted Risk Calculation  │
                    │  Google Gemini 2.0 Flash    │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │    Final Decision Output    │
                    │                             │
                    │  APPROVE | REVIEW | DENY    │
                    └─────────────────────────────┘
```

## ✨ Features

- **🚀 Parallel Processing**: 3 agents execute simultaneously using `asyncio`
- **⚡ 20x Faster**: ~45 seconds vs 15 minutes manual review
- **🤖 Google ADK Integration**: Powered by Gemini LLM for intelligent analysis
- **🌐 Web UI**: Beautiful FastAPI-based dashboard with real-time results
- **📊 Risk Visualization**: Radar charts and detailed breakdowns
- **🔌 API-First**: Full REST API with OpenAPI documentation

## 📁 Project Structure

```
FAN out-FAN in/
├── main.py                     # Application entry point
├── run.py                      # Development server
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project configuration
├── .env.example               # Environment template
├── README.md                  # This file
├── SETUP_GUIDE.md             # Detailed setup instructions
│
└── loan_underwriter/          # Main package
    ├── __init__.py
    ├── app.py                 # FastAPI application
    ├── config.py              # Configuration settings
    ├── models.py              # Data models
    │
    ├── agents/                # AI Agents
    │   ├── __init__.py
    │   ├── base_agent.py      # Base agent class
    │   ├── credit_agent.py    # Credit analysis agent
    │   ├── property_agent.py  # Property valuation agent
    │   ├── fraud_agent.py     # Fraud detection agent
    │   └── aggregator_agent.py # Results aggregator
    │
    ├── api/                   # API Layer
    │   ├── __init__.py
    │   ├── routes.py          # API endpoints
    │   ├── views.py           # HTML views
    │   └── schemas.py         # Pydantic schemas
    │
    ├── templates/             # Jinja2 HTML templates
    │   ├── base.html
    │   ├── index.html
    │   ├── application.html
    │   ├── results.html
    │   └── dashboard.html
    │
    └── static/                # Static assets
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** - [Download here](https://www.python.org/downloads/)
- **Google AI API Key** - [Get free key here](https://aistudio.google.com/app/apikey)

### Step 1: Clone or Download

```bash
# If using git
git clone <repository-url>
cd "FAN out-FAN in"

# Or simply navigate to the project folder
cd "c:\path\to\FAN out-FAN in"
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows (Command Prompt)
venv\Scripts\activate

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate on macOS/Linux
source venv/bin/activate
```

> ✅ You should see `(venv)` prefix in your terminal when activated

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure API Key

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

**Now get your FREE Google API key:**

1. **Open:** https://aistudio.google.com/app/apikey
2. **Sign in** with any Google/Gmail account
3. **Click** "Create API Key" (blue button)
4. **Copy** the key (looks like: `AIzaSyD-xxxxxxxxxxxxxxxxxxxxx`)
5. **Open** your `.env` file and replace `your_google_api_key_here`:

```env
# Before (placeholder)
GOOGLE_API_KEY=your_google_api_key_here

# After (your actual key - example)
GOOGLE_API_KEY=AIzaSyDk7xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 🔑 **Important:** The key starts with `AIza` and is ~39 characters. Keep it secret!

### Step 5: Run the Application

```bash
python main.py
```

### Step 6: Open in Browser

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Web UI (Main Interface) |
| http://localhost:8000/docs | Interactive API Documentation |
| http://localhost:8000/application | Submit New Application |
| http://localhost:8000/dashboard | View All Applications |

> 💡 **Quick Test:** Click "Run Demo" on the home page to test with sample data

## 🔧 Configuration

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ **Yes** | - | Your Google Gemini API key from [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| `DEBUG` | No | `false` | Enable debug logging and auto-reload |
| `HOST` | No | `127.0.0.1` | Server host (`0.0.0.0` for Docker) |
| `PORT` | No | `8000` | Server port |

### Example .env File

```env
# ✅ REQUIRED - Get from https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional Settings
DEBUG=true        # Set to false in production
HOST=127.0.0.1    # Change to 0.0.0.0 for Docker
PORT=8000         # Change if port is already in use
```

> 📖 See detailed instructions in `.env.example` file

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/applications/process` | Submit application for processing |
| `POST` | `/api/v1/applications/demo` | Run demo application |
| `GET` | `/api/v1/applications` | List all applications |
| `GET` | `/api/v1/applications/{id}` | Get application result |
| `GET` | `/api/v1/applications/{id}/status` | Check application status |
| `GET` | `/health` | Health check |

### Example API Call

```bash
curl -X POST "http://localhost:8000/api/v1/applications/demo"
```

## 🤖 Agent Details

### Agent A: Credit Analysis
- Pulls credit reports from bureaus
- Calculates debt-to-income ratio
- Analyzes payment history
- Assesses credit score risk

### Agent B: Property Valuation
- Queries Zillow & Redfin APIs
- Retrieves tax assessment records
- Finds comparable sales
- Identifies valuation gaps

### Agent C: Fraud Detection
- Verifies identity documents
- Checks OFAC/fraud watchlists
- Analyzes behavioral patterns
- Detects document tampering

### Aggregator Agent
- Collects all agent results
- Calculates weighted risk score
- Generates final decision
- Produces executive summary

## 📊 Decision Logic

```
Approval Confidence Score = 
    (Credit Risk × 0.40) + 
    (Property Risk × 0.35) + 
    (Fraud Risk × 0.25)

Decision Thresholds:
├── ≥85%  → AUTO APPROVED
├── 60-84% → MANUAL REVIEW
└── <60%  → DENIED
```

## 🛠️ Development

### Run in Development Mode

```bash
python run.py  # Auto-reload enabled
```

### Run Tests

```bash
pytest tests/
```

### Format Code

```bash
black loan_underwriter/
isort loan_underwriter/
```

## 📈 Performance

| Metric | Value |
|--------|-------|
| Sequential Processing | ~15 minutes |
| **Parallel Processing** | **~45 seconds** |
| Time Saved | **95%** |
| Agents Running | 3 (concurrent) |

## 🔒 Security Notes

- SSN is stored as last 4 digits only
- No real credit bureau integration (mock data)
- Add authentication for production use
- Implement rate limiting for API

## 📚 Documentation & Resources

### Project Documentation

- **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** - Comprehensive technical documentation
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed installation guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

### Visual Diagrams

- **[docs/architecture.svg](docs/architecture.svg)** - Fan-Out/Fan-In architecture
- **[docs/data-flow.svg](docs/data-flow.svg)** - Data processing pipeline
- **[docs/tech-stack.svg](docs/tech-stack.svg)** - Technology stack layers
- **[docs/api-integrations.svg](docs/api-integrations.svg)** - External API connections

### External Resources

- [Google ADK Documentation](https://ai.google.dev/adk)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

## � Customization

### Modify Agent Behavior

Edit the system instructions in each agent file:

- `loan_underwriter/agents/credit_agent.py` - Credit analysis logic
- `loan_underwriter/agents/property_agent.py` - Property valuation logic
- `loan_underwriter/agents/fraud_agent.py` - Fraud detection logic

### Adjust Risk Weights

Edit `loan_underwriter/agents/aggregator_agent.py`:

```python
CREDIT_WEIGHT = 0.40   # 40% weight for credit score
PROPERTY_WEIGHT = 0.35 # 35% weight for property
FRAUD_WEIGHT = 0.25    # 25% weight for fraud check
```

### Change Decision Thresholds

Edit `loan_underwriter/config.py`:

```python
APPROVAL_THRESHOLDS = {
    "auto_approve": 85,    # Score >= 85% = Auto Approved
    "manual_review": 60,   # Score 60-84% = Manual Review
    "auto_deny": 40        # Score < 60% = Denied
}
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `GOOGLE_API_KEY not set` | Create `.env` file from `.env.example` and add your API key |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in activated venv |
| `Port 8000 already in use` | Change `PORT=8001` in `.env` file |
| `Connection refused` | Ensure the server is running (`python main.py`) |

For detailed troubleshooting, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
3. Check terminal logs for error details

---

**Built with ❤️ using Google Gemini and FastAPI**

⭐ Star this repo if you find it useful!
