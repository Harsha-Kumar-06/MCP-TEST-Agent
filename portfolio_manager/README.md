# Automated Portfolio Manager

An intelligent, agent-based investment system built with Google ADK (Agent Development Kit) that creates personalized, data-driven investment portfolios for young investors.

## 🎯 Overview

The Automated Portfolio Manager is a multi-agent system that:
- Assesses your investment profile through an interactive questionnaire
- Analyzes macroeconomic conditions and market trends
- Identifies top-performing sectors based on economic outlook
- Selects high-quality stocks using fundamental and technical analysis
- Constructs a diversified portfolio matching your risk tolerance
- Validates the portfolio with historical backtesting
- Generates comprehensive investment reports

## 🏗️ Architecture

```
User Input → [User Profile Agent] → [Macro + Sector Agents ∥] 
→ [Stock Selection Agent] → [Portfolio Construction Agent] 
→ [Performance + Backtest Agents ∥] → [Report Synthesizer] → Final Report
```

### Agent Pipeline

| Agent | Function | Output |
|-------|----------|--------|
| **User Profile Agent** 👨‍💼 | Interactive risk assessment questionnaire | `user_profile` |
| **Macro Agent** 🌎 | Analyzes economic indicators (GDP, inflation, rates) | `macro_outlook` |
| **Sector Agent** 🏢 | Identifies optimal sectors based on conditions | `top_sectors` |
| **Stock Selection Agent** 📈 | Selects stocks using fundamental + technical analysis | `selected_stocks` |
| **Portfolio Construction Agent** ⚖️ | Allocates capital with diversification | `portfolio` |
| **Performance Agent** 📊 | Calculates Sharpe ratio, volatility, beta | `performance_report` |
| **Backtest Agent** ⏪ | Validates on 12-month historical data | `backtest_results` |
| **Report Synthesizer Agent** 📝 | Generates comprehensive client report | `final_report` |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google API Key (for Gemini models)
- Alpha Vantage API Key (free tier available)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd portfolio_manager
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Get API Keys

- **Google API Key**: [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Alpha Vantage Key**: [Free API Key](https://www.alphavantage.co/support/#api-key) (5 calls/min, 500/day)

## 💻 Usage

### Option 1: ADK Web UI (Recommended)

```bash
adk web portfolio_manager/
```

Open http://localhost:8000 in your browser.

### Option 2: FastAPI Server

```bash
uvicorn portfolio_manager.server:app --reload --port 8000
```

- Web UI: http://localhost:8001
- API Docs: http://localhost:8001/docs

### Option 3: Python API

```python
from portfolio_manager.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="portfolio_manager",
    session_service=session_service
)

# Start conversation
# The agent will guide you through the questionnaire
```

## 📊 Example Session

```
Bot: Hello! I'm your AI Portfolio Manager. Let's create a personalized 
     investment portfolio. How much would you like to invest?

You: $10,000

Bot: Great! $10,000 is a solid starting point. Now, what's your primary 
     investment goal?
     1. Preserve capital (low risk)
     2. Generate regular income
     3. Balanced growth and income
     4. Aggressive growth
     5. Maximum growth (highest risk)

You: Balanced growth

Bot: Good choice. What's your investment time horizon?
...

[After questionnaire completion]

Bot: Based on your profile:
     - Risk Score: 6/10 (Moderately Aggressive)
     - Capital: $10,000
     - Time Horizon: 5-10 years
     
     Analyzing market conditions...
     
[Final Portfolio Report]
# Portfolio Investment Report
## YOUR PERSONALIZED PORTFOLIO

| Stock | Sector | Allocation | Shares | Value |
|-------|--------|------------|--------|-------|
| AAPL  | Technology | 18% | 12 | $1,800 |
| MSFT  | Technology | 15% | 4 | $1,500 |
| UNH   | Healthcare | 12% | 2 | $1,200 |
...

## EXPECTED PERFORMANCE
- Expected Annual Return: 12.5%
- Portfolio Sharpe Ratio: 1.35
- Volatility: 15.2%
```

## 🛠️ Project Structure

```
portfolio_manager/
├── __init__.py                    # Package init, exports root_agent
├── agent.py                       # Root agent orchestration
├── server.py                      # FastAPI server
├── requirements.txt               # Dependencies
├── .env.example                   # Environment template
├── sub_agents/
│   ├── user_profile_agent.py     # Risk assessment
│   ├── macro_agent.py            # Economic analysis
│   ├── sector_agent.py           # Sector selection
│   ├── stock_selection_agent.py  # Stock picking
│   ├── portfolio_construction_agent.py  # Allocation
│   ├── performance_agent.py      # Metrics calculation
│   ├── backtest_agent.py         # Historical validation
│   └── report_synthesizer_agent.py  # Report generation
├── tools/
│   ├── stock_api.py              # Alpha Vantage integration
│   ├── calculations.py           # Financial math
│   └── macro_data.py             # Economic indicators
├── data/
│   ├── sector_correlations.json  # Sector performance matrix
│   ├── stock_universe.json       # Curated stock list
│   └── risk_profiles.json        # Allocation rules
└── tests/
    ├── test_calculations.py
    └── test_stock_api.py
```

## 📈 Data Sources

### Alpha Vantage API
- Real-time stock quotes
- Company fundamentals (P/E, revenue, margins)
- Technical indicators (RSI, MACD, SMA)
- Historical price data
- Economic indicators (GDP, CPI, unemployment, Fed rate)

### Rate Limits
- Free tier: 5 API calls/minute, 500 calls/day
- The system includes intelligent rate limiting with exponential backoff

## 🔧 Configuration

### Risk Profile Settings

Edit `data/risk_profiles.json` to customize:
- Allocation percentages per risk level
- Maximum position sizes
- Sector constraints
- Minimum diversification requirements

### Stock Universe

Edit `data/stock_universe.json` to:
- Add/remove stocks per sector
- Update stock classifications
- Modify ETF mappings

## 🧪 Testing

Run unit tests:
```bash
pytest portfolio_manager/tests/ -v
```

Run with coverage:
```bash
pytest portfolio_manager/tests/ --cov=portfolio_manager --cov-report=html
```

## ⚠️ Disclaimer

This is an educational project demonstrating AI-powered portfolio construction. It is **NOT** financial advice.

- Past performance does not guarantee future results
- All investments carry risk including loss of principal
- The backtesting uses historical data with hindsight bias
- Market conditions change and models may not adapt quickly
- Always consult a qualified financial advisor before investing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Related Projects

- [PR Code Reviewer](../pr_code_reviewer/) - Similar ADK architecture
- [Access Controller Agent](../access_controller_agent/) - Tool-based agent example
- [Research Assistant](../research_assistant/) - Complex agent orchestration
