# Portfolio Swarm - Complete Setup & Project Guide

## 📖 Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [System Requirements](#system-requirements)
4. [Installation Guide](#installation-guide)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [Usage Guide](#usage-guide)
8. [Understanding the Agents](#understanding-the-agents)
9. [Optimization Flow](#optimization-flow)
10. [API Reference](#api-reference)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Configuration](#advanced-configuration)

---

## Introduction

The **Portfolio Swarm System** is a multi-agent collaborative AI system designed for intelligent portfolio optimization. It employs the **swarm pattern** where 5 specialized AI agents work together to analyze, debate, and reach consensus on the best portfolio rebalancing strategy.

### Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **5 Specialized Agents** | Market, Risk, Tax, ESG, and Trading agents |
| 🧠 **AI-Powered** | Google Gemini AI (gemini-2.5-flash) integration |
| 🌐 **Multiple Interfaces** | Web UI, CLI, REST API, Streamlit |
| 💬 **Natural Language** | Describe your portfolio in plain text |
| 📁 **File Support** | CSV, JSON, YAML file uploads |
| 🗳️ **Consensus Voting** | Democratic decision-making process |
| 🔄 **Iterative Debate** | Agents refine proposals through discussion |
| 📊 **Real-time Progress** | Watch optimization in real-time |

---

## Architecture Overview

### High-Level Architecture Diagram

![Architecture Diagram](diagrams/architecture.svg)

The system is organized in layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                         │
│   Flask Web UI │ CLI Interface │ Streamlit │ REST API          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    ORCHESTRATOR LAYER                           │
│   SwarmOrchestrator - Manages iterations, consensus, phases     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    COMMUNICATION LAYER                          │
│   CommunicationBus - Message routing, history, pub/sub          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     AGENT LAYER                                 │
│   Market │ Risk │ Tax │ ESG │ Trading  (All AI-powered)         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS                        │
│   Gemini AI │ File Parsers │ Market Data │ ESG Data             │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Interaction Model

![Agent Interaction](diagrams/agent-interaction.svg)

### Core Components

| Component | File | Description |
|-----------|------|-------------|
| **Orchestrator** | `portfolio_swarm/orchestrator.py` | Coordinates all agents, manages iterations |
| **Communication Bus** | `portfolio_swarm/communication.py` | Message routing between agents |
| **Base Agent** | `portfolio_swarm/base_agent.py` | Abstract base class for all agents |
| **Agents** | `portfolio_swarm/agents.py` | 5 specialized AI agents |
| **Models** | `portfolio_swarm/models.py` | Data models (Portfolio, Trade, Vote) |
| **Config** | `portfolio_swarm/config.py` | API keys, model settings |
| **Strategies** | `portfolio_swarm/strategies.py` | Optimization strategies |

---

## System Requirements

### Minimum Requirements

- **Python**: 3.9 or higher
- **Memory**: 4GB RAM
- **Disk**: 500MB free space
- **Network**: Internet connection (for Gemini API)

### Dependencies

```
Flask>=3.0.0          # Web framework
python-dotenv>=1.0.0  # Environment variables
pyyaml>=6.0.1         # YAML file parsing
openpyxl>=3.1.2       # Excel file parsing
google-generativeai>=0.3.0  # Gemini AI
streamlit>=1.30.0     # Alternative UI (optional)
pandas>=2.0.0         # Data manipulation
```

---

## Installation Guide

### Step 1: Clone/Download the Project

```bash
# Navigate to your workspace
cd your-workspace-folder

# The project should be in: Swarm Pattern/
```

### Step 2: Create Virtual Environment (Recommended)

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up API Key

1. Get a free Gemini API key from: https://makersuite.google.com/app/apikey

2. Create `.env` file in the project root:

```env
# Required
GEMINI_API_KEY=your-api-key-here

# Optional Configuration
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_TOKENS=2048
ENABLE_COST_TRACKING=true
ENABLE_DEBUG_LOGGING=false
```

### Step 5: Verify Installation

```bash
python -c "from portfolio_swarm.config import GeminiConfig; print('✅ Setup complete!' if GeminiConfig.validate() else '❌ API key not configured')"
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Your Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model to use |
| `GEMINI_TEMPERATURE` | `0.3` | Response creativity (0-1) |
| `GEMINI_MAX_TOKENS` | `2048` | Maximum response length |
| `ENABLE_COST_TRACKING` | `true` | Track API usage costs |
| `ENABLE_DEBUG_LOGGING` | `false` | Enable debug output |

### Orchestrator Configuration

```python
orchestrator = SwarmOrchestrator(
    agents=agents,
    max_iterations=10,        # Maximum debate rounds (1-20)
    min_iterations=1,         # Minimum before consensus
    consensus_threshold=0.6,  # Required approval rate (0.5-1.0)
    require_unanimous=False,  # Require 100% approval
    strategy=strategy         # Optimization strategy
)
```

### Available Strategies

| Strategy | Description | Risk Focus |
|----------|-------------|------------|
| `BALANCED` | Equal weight to all factors | Medium |
| `AGGRESSIVE_GROWTH` | Maximize returns | High |
| `CONSERVATIVE` | Preserve capital | Low |
| `TAX_EFFICIENT` | Minimize tax liability | N/A |
| `ESG_FOCUSED` | Prioritize sustainability | Medium |
| `INCOME_FOCUSED` | Maximize dividends | Low-Medium |
| `SECTOR_ROTATION` | Dynamic sector allocation | Medium-High |
| `RISK_PARITY` | Equal risk contribution | Low |

---

## Running the Application

### Option 1: Web UI (Recommended)

**Double-click:** `run_web.bat`

**Or command line:**
```bash
python flask_ui.py
```

Then open: http://localhost:5000

### Option 2: Command Line Interface

**Double-click:** `run_cli.bat`

**Or command line:**
```bash
python cli_interface.py
```

### Option 3: Demo Script

**Double-click:** `run_demo.bat`

**Or command line:**
```bash
python demo.py
```

### Option 4: Streamlit UI (Alternative)

```bash
streamlit run web_ui.py
```

---

## Usage Guide

### Web UI Workflow

![Flow Chart](diagrams/flowchart.svg)

#### 1. Load Portfolio

Choose one of three methods:

**📊 Sample Portfolio**
- Click "Load Sample Portfolio" button
- Pre-built $50M demo portfolio loads automatically

**📝 Text Description**
```
My Investment Portfolio:

I have $50,000 invested in Apple (AAPL) bought at $150, now at $185.
Also 200 shares of Microsoft (MSFT) at $280, currently $420.
100 Tesla (TSLA) shares at $200, now $175.
$25,000 in Amazon (AMZN) at $130, now $178.
500 NVIDIA (NVDA) shares at $450, currently $890.

Risk tolerance: moderate
Goal: long-term growth
```

**📁 File Upload**
- Supported formats: CSV, JSON, YAML
- See `samples/` folder for templates

#### 2. Configure Settings

| Setting | Range | Description |
|---------|-------|-------------|
| Max Iterations | 1-20 | Maximum debate rounds |
| Consensus Threshold | 50-100% | Required approval rate |
| Strategy | 8 options | Optimization approach |
| Enabled Agents | Checkboxes | Which agents participate |

#### 3. Run Optimization

1. Click **"Run Optimization"** button
2. Watch real-time progress:
   - Analysis phase
   - Debate phase (if iteration > 1)
   - Proposal generation
   - Voting phase
3. View results when complete

#### 4. Review Results

- **Agent Votes**: Each agent's vote with rationale
- **Trade Plan**: Approved buy/sell recommendations
- **Tax Implications**: Estimated tax impact
- **Execution Timeline**: Recommended trading schedule

---

## Understanding the Agents

### 📈 Market Analysis Agent

**Role**: Evaluate market conditions and valuations

**Capabilities**:
- PE ratio analysis vs. historical averages
- Sector trend identification
- Market sentiment signals
- Valuation recommendations

**Typical Output**:
```
FINDINGS: Technology sector trading at 32.5x PE vs 24x historical average - overvalued.
RECOMMENDATION: Reduce tech exposure by 5-10%.
CONVICTION: 8/10
```

### ⚠️ Risk Assessment Agent

**Role**: Ensure portfolio compliance and manage risk

**Capabilities**:
- Policy limit checking
- Beta/VaR analysis
- Concentration risk assessment
- Compliance violation detection

**Typical Output**:
```
FINDINGS: CRITICAL - Technology at 32.2% exceeds 30% policy limit.
RECOMMENDATION: Immediate rebalancing required for compliance.
CONVICTION: 10/10
```

### 💰 Tax Strategy Agent

**Role**: Optimize tax implications of trades

**Capabilities**:
- Short-term vs. long-term gain analysis
- Tax lot optimization
- Loss harvesting opportunities
- Wash sale rule compliance

**Typical Output**:
```
FINDINGS: Selling NVDA triggers $250K short-term gains (37% rate).
RECOMMENDATION: Consider partial sale or wait 2 months for long-term rate.
CONVICTION: 7/10
```

### 🌱 ESG Compliance Agent

**Role**: Ensure environmental, social, governance standards

**Capabilities**:
- ESG score analysis
- Sustainability metrics
- Controversy screening
- Green investment alignment

**Typical Output**:
```
FINDINGS: Portfolio ESG score 72/100. XOM below minimum threshold of 50.
RECOMMENDATION: Replace XOM with higher ESG alternative in energy sector.
CONVICTION: 6/10
```

### 🤖 Algorithmic Trading Agent

**Role**: Plan trade execution strategy

**Capabilities**:
- Execution timeline planning
- VWAP/TWAP strategy selection
- Liquidity analysis
- Slippage/cost estimation

**Typical Output**:
```
FINDINGS: $5M trade executable in 1-2 days with minimal slippage.
RECOMMENDATION: Use VWAP over 2 hours for larger positions.
CONVICTION: 8/10
ESTIMATED_COST: $537
```

---

## Optimization Flow

### Phase 1: Parallel Analysis

All 5 agents analyze the portfolio independently and simultaneously.

```
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│  Market    │  │   Risk     │  │    Tax     │  │    ESG     │  │  Trading   │
│  Analysis  │  │ Assessment │  │  Strategy  │  │ Compliance │  │  Planning  │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      │               │               │               │               │
      └───────────────┴───────────────┼───────────────┴───────────────┘
                                      ▼
                        Findings broadcast to all agents
```

### Phase 2: Inter-Agent Debate

Agents challenge each other's conclusions:

```
Market Agent: "Tech is overvalued, recommend reducing NVDA"
Tax Agent:    "But selling NVDA triggers $250K in short-term gains!"
Risk Agent:   "Compliance violation is critical - must reduce tech"
ESG Agent:    "Ensure replacements meet ESG minimums"
Trading:      "Can execute in 2 days with low slippage"
```

### Phase 3: Proposal Generation

Each agent proposes a trade plan:

```python
Proposal = {
    "trades": [
        {"action": "SELL", "ticker": "NVDA", "shares": 100, "value": 89000},
        {"action": "BUY", "ticker": "JNJ", "shares": 50, "value": 44500},
        {"action": "BUY", "ticker": "PFE", "shares": 100, "value": 44500}
    ],
    "conviction": 8,
    "rationale": "Reduce tech, add healthcare for balance"
}
```

### Phase 4: Voting

All agents vote on the best proposal:

| Agent | Vote | Score | Rationale |
|-------|------|-------|-----------|
| Market | ✅ APPROVE | 8/10 | Addresses overvaluation |
| Risk | ✅ APPROVE | 10/10 | Fixes compliance violation |
| Tax | ✅ APPROVE | 7/10 | Acceptable tax impact |
| ESG | ✅ APPROVE | 6/10 | ESG scores maintained |
| Trading | ✅ APPROVE | 8/10 | Feasible execution |

**Result**: 80% approval → **Consensus Reached!**

---

## API Reference

### Core Classes

#### SwarmOrchestrator

```python
from portfolio_swarm.orchestrator import SwarmOrchestrator

orchestrator = SwarmOrchestrator(
    agents=agents,           # List of BaseAgent instances
    max_iterations=10,       # Max debate rounds
    min_iterations=1,        # Min before consensus
    consensus_threshold=0.6, # Required approval rate
    require_unanimous=False, # Require 100% approval
    progress_callback=None,  # Progress reporting function
    strategy=None            # OptimizationStrategy
)

result = orchestrator.run_rebalancing_swarm(portfolio)
```

#### Portfolio

```python
from portfolio_swarm.models import Portfolio, Position

portfolio = Portfolio(
    positions=[Position(...)],
    cash=50000.0,
    policy_limits={"technology_limit": 30}
)
```

#### Position

```python
from datetime import datetime
from portfolio_swarm.models import Position

position = Position(
    ticker="AAPL",
    shares=100,
    current_price=185.0,
    cost_basis=150.0,
    acquisition_date=datetime(2023, 1, 15),
    sector="Technology",
    esg_score=75,
    beta=1.2
)
```

### Progress Callback

```python
def progress_callback(iteration: int, phase: str, details: str):
    print(f"[{iteration}] {phase}: {details}")

orchestrator = SwarmOrchestrator(
    agents=agents,
    progress_callback=progress_callback
)
```

---

## Troubleshooting

### Common Issues

#### ❌ "GEMINI_API_KEY not configured"

**Solution**: Create `.env` file with valid API key:
```env
GEMINI_API_KEY=your-actual-api-key
```

#### ❌ "API quota exhausted"

**Causes**: 
- Daily API limit reached
- Too many requests too quickly

**Solutions**:
1. Wait for quota reset (usually 24 hours)
2. Reduce number of iterations
3. Use fewer agents
4. Upgrade API plan

#### ❌ "No consensus reached"

**Solutions**:
1. Increase `max_iterations` (try 15-20)
2. Lower `consensus_threshold` (try 0.5)
3. Simplify portfolio (fewer positions)
4. Use more conservative strategy

#### ❌ Import errors

**Solution**: Ensure virtual environment is activated and dependencies installed:
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Debug Mode

Enable debug logging in `.env`:
```env
ENABLE_DEBUG_LOGGING=true
```

Check logs in `logs/` folder.

---

## Advanced Configuration

### Custom Strategy

```python
from portfolio_swarm.strategies import create_custom_strategy

custom = create_custom_strategy(
    name="My Strategy",
    description="Custom optimization approach",
    risk_weight=0.3,
    return_weight=0.4,
    tax_weight=0.1,
    esg_weight=0.2
)
```

### Custom Agent Weights

Modify consensus calculation by adjusting agent conviction scores:

```python
class CustomMarketAgent(MarketAnalysisAgent):
    def vote_on_proposal(self, proposal, portfolio):
        vote = super().vote_on_proposal(proposal, portfolio)
        vote.conviction = min(10, vote.conviction + 2)  # Boost weight
        return vote
```

### Programmatic Usage

```python
from portfolio_swarm.agents import (
    MarketAnalysisAgent, RiskAssessmentAgent, TaxStrategyAgent,
    ESGComplianceAgent, AlgorithmicTradingAgent
)
from portfolio_swarm.communication import CommunicationBus
from portfolio_swarm.orchestrator import SwarmOrchestrator
from portfolio_swarm.models import Portfolio, Position
from datetime import datetime

# Create communication bus
comm_bus = CommunicationBus()

# Create agents
agents = [
    MarketAnalysisAgent(comm_bus),
    RiskAssessmentAgent(comm_bus),
    TaxStrategyAgent(comm_bus),
    ESGComplianceAgent(comm_bus),
    AlgorithmicTradingAgent(comm_bus)
]

# Create portfolio
portfolio = Portfolio(
    positions=[
        Position(
            ticker="AAPL", shares=100, current_price=185.0,
            cost_basis=150.0, acquisition_date=datetime(2023, 1, 15),
            sector="Technology", esg_score=75, beta=1.2
        )
    ],
    cash=50000.0,
    policy_limits={"technology_limit": 30}
)

# Create orchestrator and run
orchestrator = SwarmOrchestrator(
    agents=agents,
    max_iterations=10,
    consensus_threshold=0.6
)

result = orchestrator.run_rebalancing_swarm(portfolio)

if result.consensus_reached:
    print("✅ Consensus reached!")
    print(f"Approval rate: {result.approval_rate:.0%}")
    for trade in result.trade_plan.trades:
        print(f"  {trade.action}: {trade.ticker} - ${trade.value:,.0f}")
else:
    print("❌ No consensus - using fallback strategy")
```

---

## 📚 Additional Resources

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed technical architecture
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [INPUTS_OUTPUTS.md](INPUTS_OUTPUTS.md) - Input/output formats
- [GEMINI_SETUP.md](GEMINI_SETUP.md) - Gemini API setup details
- [samples/](../samples/) - Sample portfolio files

---

## 📄 License

This project is for educational and demonstration purposes.

---

*Last updated: February 2026*
*Version: 2.0*
