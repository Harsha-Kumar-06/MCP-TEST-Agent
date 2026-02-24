# 📚 Portfolio Swarm - Complete Documentation

## 📋 Table of Contents
- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Core Features](#-core-features)
- [Iteration Flow](#-iteration-flow)
- [Voting & Consensus](#-voting--consensus)
- [Proposal Adaptation](#-proposal-adaptation)
- [Agent Communication](#-agent-communication)
- [Agent Pipeline](#-agent-pipeline-detailed)
- [Strategies](#-strategies)
- [Supported Input Formats](#-supported-input-formats)
- [Data Flow](#-data-flow)
- [API Reference](#-api-reference)
- [Technical Stack](#-technical-stack)
- [Installation & Setup](#-installation--setup)
- [Performance](#-performance)
- [Security & Privacy](#-security--privacy)
- [Use Cases](#-use-cases)
- [Test Files](#-test-files)

---

## 🎯 Overview

Portfolio Swarm is an advanced **multi-agent AI system** built with the **Swarm Pattern** for collaborative portfolio optimization. It coordinates 5 specialized AI agents that analyze, debate, propose, and vote on trade plans to reach consensus.

### Key Highlights

| Feature | Description |
|---------|-------------|
| **Framework** | Swarm Pattern with Consensus Voting |
| **LLM** | Google Gemini 2.5 Flash |
| **Architecture** | 5 specialized agents working collaboratively |
| **Input Support** | Text, CSV, JSON, YAML portfolio formats |
| **Strategies** | 10+ optimization strategies with star ratings |
| **Consensus** | Configurable 60-100% approval threshold |
| **Adaptation** | Proposals shrink until consensus reached |

### 🆕 Recent Enhancements
- **Data-Driven Voting**: Agents use quality scores (0-100) instead of hardcoded logic
- **Rejection Feedback Loop**: Proposals adapt based on agent concerns
- **Enhanced Timeline**: Full iteration history with proposal details
- **Strategy-Adaptive Ratings**: Stars rated based on YOUR portfolio

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

![System Architecture](diagrams/architecture.svg)

### Component Interaction Overview

| Component | Role | Communication |
|-----------|------|---------------|
| **Orchestrator** | Central coordinator | Controls all phases |
| **Communication Bus** | Message router | Pub/Sub pattern |
| **5 Agents** | Specialized analyzers | Via bus + direct |
| **Models** | Data structures | Shared state |

---

## ✨ Core Features

### 1. Multi-Agent Collaboration

🤖 **5 Specialized AI Agents** working in concert:
- Market Analysis - Valuations & trends
- Risk Assessment - Compliance & VaR
- Tax Strategy - Tax loss harvesting
- ESG Compliance - Sustainability screening
- Algorithmic Trading - Execution feasibility

### 2. Flexible Input Support

📄 **Multiple Input Formats**:
- Natural language text descriptions
- CSV spreadsheet uploads
- JSON structured data
- YAML configuration files

### 3. Consensus-Based Decision Making

🗳️ **Democratic Voting System**:
- Configurable threshold (60-100%)
- Score-based voting (0-100)
- Full audit trail
- Rejection feedback loop

### 4. Strategy Selection

📊 **10+ Optimization Strategies**:
- Aggressive Growth ⭐⭐⭐⭐
- Conservative Income ⭐⭐⭐⭐⭐
- Balanced ⭐⭐⭐⭐
- Tax Efficient ⭐⭐⭐
- ESG Focused ⭐⭐⭐⭐
- Risk Minimization ⭐⭐⭐⭐⭐
- And more...

### 5. Adaptive Proposals

🔄 **Rejection Feedback Loop**:
- Proposals shrink each iteration
- Agents learn from rejections
- Size multiplier: `max(0.3, 1.0 - iter × 0.15)`
- Additional reductions for specific concerns

### 6. Real-Time Progress

📡 **Live Updates**:
- Watch agents debate in real-time
- See voting as it happens
- Full iteration timeline
- Detailed proposal breakdowns

---

## 🔄 Iteration Flow

### Sequential Pipeline Flow Diagram

![Optimization Flowchart](diagrams/flowchart.svg)

### Phase Descriptions

| Phase | Action | Duration |
|-------|--------|----------|
| **1. Analysis** | All agents analyze portfolio in parallel | 2-5 sec |
| **2. Debate** | Agents discuss findings via comm bus | 2-5 sec |
| **3. Proposals** | Each agent generates trade plan | 3-8 sec |
| **4. Voting** | Score-based voting (0-100) | 2-5 sec |
| **5. Consensus** | Check threshold, loop or exit | Instant |

---

## 🗳️ Voting & Consensus

### Consensus Voting Mechanism

![Voting Mechanism](diagrams/voting-mechanism.svg)

### Voting Thresholds

| Score | Vote | Description |
|-------|------|-------------|
| **≥70** | ✅ Approve | Proposal meets agent criteria |
| **60-69** | ⚪ Abstain | Neutral, no strong opinion |
| **<60** | ❌ Reject | Significant concerns |

### Consensus Requirements

| Setting | Value | Effect |
|---------|-------|--------|
| `consensus_threshold` | 0.6-1.0 | Minimum approval rate |
| `min_iterations` | 1-10 | Force N debate rounds |
| `max_iterations` | 1-10 | Cap on total rounds |
| `require_unanimous` | bool | All agents must approve |

---

## 📉 Proposal Adaptation

### Adaptation Loop Diagram

![Proposal Adaptation](diagrams/proposal-adaptation.svg)

### Size Reduction Formula

```python
size_multiplier = max(0.3, 1.0 - (iteration * 0.15))

# Additional reductions based on feedback
if "large" in rejection_feedback:
    size_multiplier *= 0.5
if "illiquid" in rejection_feedback:
    size_multiplier *= 0.7
```

### Iteration Progression Example

| Iteration | Notional | Trades | Result |
|-----------|----------|--------|--------|
| 1 | $10.8M | 4 | ❌ Rejected |
| 2 | $5.8M | 4 | ❌ Rejected |
| 3 | $4.8M | 3 | ❌ Rejected |
| 4 | $2.7M | 3 | ✅ Approved |

---

## 📡 Agent Communication

### Communication Pattern Diagram

![Agent Interaction](diagrams/agent-interaction.svg)

### Message Types

| Type | Purpose | Routing |
|------|---------|--------|
| **Analysis** | Share findings | Broadcast |
| **Debate** | Challenge/support | Targeted |
| **Proposal** | Submit trade plan | To orchestrator |
| **Vote** | Cast vote + rationale | To orchestrator |

---

## 🤖 Agent Pipeline (Detailed)

### Agent 1: MarketAnalysisAgent

**Purpose**: Analyze market valuations, trends, and sentiment

**Processing Steps**:
1. Fetch current prices and market data
2. Calculate sector allocation percentages
3. Identify overweight/underweight positions
4. Generate trade recommendations

**Key Metrics**:
- Price targets
- Sector rotation signals
- Momentum indicators
- Valuation ratios

---

### Agent 2: RiskAssessmentAgent

**Purpose**: Evaluate compliance, VaR, and risk exposure

**Processing Steps**:
1. Check policy limit violations
2. Calculate portfolio beta and VaR
3. Identify concentration risks
4. Assess liquidity constraints

**Severity Ratings**:
- 🔴 **High**: Immediate violations
- 🟡 **Medium**: Approaching limits
- 🟢 **Low**: Within tolerance

---

### Agent 3: TaxStrategyAgent

**Purpose**: Optimize tax efficiency of trades

**Processing Steps**:
1. Identify tax lots (FIFO, LIFO, specific ID)
2. Calculate unrealized gains/losses
3. Find tax-loss harvesting opportunities
4. Avoid wash sale violations

**Tax Categories**:
- **STCG**: Held < 1 year (taxed as income)
- **LTCG**: Held ≥ 1 year (preferential rate)

---

### Agent 4: ESGComplianceAgent

**Purpose**: Ensure ESG standards are maintained

**Processing Steps**:
1. Check position ESG scores
2. Calculate weighted average ESG
3. Identify low-ESG positions
4. Screen for controversies

**ESG Thresholds**:
- Position minimum: 40
- Portfolio average minimum: 60
- Sector exclusions where applicable

---

### Agent 5: AlgorithmicTradingAgent

**Purpose**: Evaluate execution feasibility

**Processing Steps**:
1. Assess liquidity (ADV analysis)
2. Calculate market impact
3. Determine optimal execution strategy
4. Flag illiquid positions

**Execution Strategies**:
- **VWAP**: Volume-weighted average price
- **TWAP**: Time-weighted average price
- **IS**: Implementation shortfall

---

## 📊 Strategies

### Available Strategy Types

| Strategy | Risk | Focus | Star Rating |
|----------|------|-------|-------------|
| `AGGRESSIVE_GROWTH` | High | Growth stocks, momentum | ⭐⭐⭐⭐ |
| `CONSERVATIVE_INCOME` | Low | Dividends, stability | ⭐⭐⭐⭐⭐ |
| `BALANCED` | Medium | Diversification | ⭐⭐⭐⭐ |
| `TAX_EFFICIENT` | Medium | Tax optimization | ⭐⭐⭐ |
| `ESG_FOCUSED` | Medium | Sustainability | ⭐⭐⭐⭐ |
| `RISK_MINIMIZATION` | Low | Volatility reduction | ⭐⭐⭐⭐⭐ |
| `SECTOR_ROTATION` | High | Tactical allocation | ⭐⭐⭐ |
| `DIVIDEND_GROWTH` | Low | Income growth | ⭐⭐⭐⭐ |
| `MOMENTUM` | High | Trend following | ⭐⭐⭐ |
| `VALUE_INVESTING` | Medium | Undervalued stocks | ⭐⭐⭐⭐ |

### Strategy Selection Code

```python
from portfolio_swarm.strategies import get_strategy, StrategyType

strategy = get_strategy(StrategyType.AGGRESSIVE_GROWTH)
# strategy.name, strategy.risk_tolerance, strategy.sector_preferences
```

---

## 📁 Supported Input Formats

| Category | Formats | Parser |
|----------|---------|--------|
| **Text** | Natural language descriptions | Gemini AI |
| **Structured** | `.csv`, `.json`, `.yaml` | Native Python |
| **Templates** | Predefined formats | Template engine |

### Input Fields

| Field | Required | Description |
|-------|----------|-------------|
| `ticker` | ✅ | Stock symbol (e.g., AAPL) |
| `shares` | ✅ | Number of shares |
| `cost_basis` | ✅ | Average purchase price |
| `current_price` | ✅ | Current market price |
| `acquisition_date` | ✅ | Purchase date |
| `sector` | ⚪ | Industry sector |
| `esg_score` | ⚪ | ESG rating (0-100) |
| `beta` | ⚪ | Market beta (default: 1.0) |

---

## 📈 Data Flow

### Data Flow Diagram

![Data Flow](diagrams/data-flow.svg)

---

## 🌐 API Reference

### POST /api/optimize

Run portfolio optimization

```python
# Request
{
  "portfolio": {...},
  "strategy": "AGGRESSIVE_GROWTH",
  "consensus_threshold": 0.8,
  "max_iterations": 5
}

# Response
{
  "success": true,
  "approved": true,
  "approval_rate": 0.8,
  "trade_plan": [...],
  "iteration_history": [...]
}
```

### POST /api/parse

Parse natural language portfolio description

```python
# Request
{
  "text": "I have 2200 shares of NVIDIA at $420..."
}

# Response
{
  "success": true,
  "portfolio": {...},
  "positions_found": 6
}
```

### GET /api/strategies

List available strategies

```python
# Response
{
  "strategies": [
    {"name": "AGGRESSIVE_GROWTH", "stars": 4, "risk": "high"},
    {"name": "BALANCED", "stars": 4, "risk": "medium"},
    ...
  ]
}
```

### SwarmOrchestrator Class

```python
orchestrator = SwarmOrchestrator(
    agents: List[BaseAgent],        # 5 specialized agents
    max_iterations: int = 10,       # Maximum debate rounds
    min_iterations: int = 1,        # Force at least N rounds
    consensus_threshold: float = 0.6,  # 60-100% approval needed
    require_unanimous: bool = False,   # Require all agents to agree
    progress_callback=None,         # Real-time updates callback
    strategy: OptimizationStrategy = None  # Trading strategy
)

result = orchestrator.run_rebalancing_swarm(portfolio)
# Returns: ConsensusResult with trade_plan, approval_rate, votes
```

### Portfolio Model

```python
portfolio = Portfolio(
    positions: List[Position],      # Stock holdings
    cash: float,                    # Available cash
    policy_limits: Dict = None      # Constraints (tech_limit, min_esg, max_beta)
)

Position(
    ticker: str,
    shares: int,
    cost_basis: float,
    current_price: float,
    acquisition_date: datetime,
    sector: str,
    esg_score: float = 50.0,
    beta: float = 1.0
)
```

---

## 🛠️ Technical Stack

### Backend

| Component | Technology |
|-----------|------------|
| **Framework** | Flask |
| **LLM** | Google Gemini 2.5 Flash |
| **Agent Pattern** | Swarm with Consensus |
| **Session** | In-memory |
| **Logging** | Python logging |

### Frontend

| Component | Technology |
|-----------|------------|
| **UI** | HTML5/CSS3/JavaScript |
| **Styling** | Custom dark theme |
| **Charts** | Inline pie charts |
| **Updates** | Real-time progress |

### Core Modules

| Module | File | Description |
|--------|------|-------------|
| **Orchestrator** | `orchestrator.py` | Iteration cycles, consensus tracking |
| **Base Agent** | `base_agent.py` | Caching, feedback, voting |
| **Agents** | `agents.py` | 5 specialized agents |
| **Models** | `models.py` | Portfolio, Position, Trade, Vote |
| **Communication** | `communication.py` | Message routing, pub/sub |
| **Strategies** | `strategies.py` | 10+ optimization strategies |
| **Text Parser** | `text_parser.py` | Natural language parsing |

---

## 🚀 Installation & Setup

### 1. Prerequisites

```bash
Python 3.8 or higher
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.5
GEMINI_MAX_TOKENS=4096
```

Get API keys:
- **Gemini API**: https://aistudio.google.com/app/apikey

### 4. Run Server

```bash
python flask_ui.py
```

### 5. Access Application

Open browser: http://localhost:5000

---

## 📊 Performance

| Operation | Duration |
|-----------|----------|
| Portfolio Parsing | 2-5 seconds |
| Single Iteration | 10-20 seconds |
| Full Optimization (5 iter) | 60-120 seconds |
| API Call (per agent) | 2-4 seconds |

---

## 🔒 Security & Privacy

| Feature | Implementation |
|---------|----------------|
| **Data Storage** | In-memory only, no persistence |
| **API Keys** | Environment variables |
| **Sessions** | Per-request, no tracking |
| **Content Filtering** | Gemini safety settings |

---

## 🎯 Use Cases

| Use Case | Description |
|----------|-------------|
| **Portfolio Rebalancing** | Optimize existing holdings |
| **Risk Reduction** | Reduce concentration/beta |
| **Tax Optimization** | Harvest losses, defer gains |
| **ESG Compliance** | Meet sustainability targets |
| **Strategy Shifts** | Change from growth to income |
| **New Allocation** | Deploy cash into diversified positions |

---

## 🧪 Test Files

| Test | Purpose |
|------|---------|
| `test_unit.py` | Proposal adaptation, voting logic (no API) |
| `test_integration.py` | Full swarm with real API calls |
| `test_comprehensive.py` | Multiple portfolios and strategies |

### Running Tests

```bash
# Unit tests (fast, no API)
python test_unit.py

# Integration tests (requires API key)
python test_integration.py

# Comprehensive tests
python test_comprehensive.py
```

---

<p align="center">
  <b>Built with Swarm Pattern + Google Gemini AI</b><br>
  <i>Portfolio Swarm v1.0</i>
</p>
