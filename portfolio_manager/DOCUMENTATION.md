# Automated Portfolio Manager - Complete Technical Documentation

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Conversation Flow](#conversation-flow)
4. [Sequential Pipeline](#sequential-pipeline)
5. [Sub-Agents Deep Dive](#sub-agents-deep-dive)
6. [Tools & APIs](#tools--apis)
7. [Data Sources](#data-sources)
8. [API Rate Limiting](#api-rate-limiting)
9. [Agent-to-Agent (A2A) Protocol](#agent-to-agent-a2a-protocol)
10. [Deployment Guide](#deployment-guide)
11. [Testing & Validation](#testing--validation)
12. [Troubleshooting](#troubleshooting)

---

## Executive Summary

The **Automated Portfolio Manager** is an intelligent multi-agent system built with **Google ADK (Agent Development Kit)** that creates personalized, data-driven investment portfolios for individual investors. Unlike traditional robo-advisors that use static rules, this system employs **7 specialized AI agents** working in sequence to analyze economic conditions, select optimal sectors, pick quality stocks, construct diversified portfolios, and validate strategies with historical data.

### Key Capabilities
- **Conversational Profile Collection**: Natural language interaction to understand investor goals and risk tolerance
- **Real-Time Market Analysis**: Fetches live economic indicators (GDP, inflation, unemployment, interest rates)
- **Fundamental & Technical Analysis**: Evaluates stocks using P/E ratios, revenue growth, RSI, MACD
- **Risk-Based Allocation**: Constructs portfolios matching investor risk profiles (1-10 scale)
- **Historical Backtesting**: Validates portfolios against 12 months of real market data
- **Comprehensive Reporting**: Generates detailed markdown reports with performance metrics

### Technology Stack
- **Framework**: Google ADK (gemini-2.0-flash model)
- **API Server**: FastAPI with async support
- **Data Source**: Alpha Vantage API (free tier: 5 calls/min)
- **Agent Pattern**: Sequential execution to respect API rate limits
- **Protocols**: REST API + A2A Protocol for agent interoperability

---

## System Architecture

![System Architecture](docs/system_architecture.svg)

### Architecture Layers

#### 1. User Interface Layer
Three interfaces provide access to the agent:

- **Web UI (HTML/CSS/JS)**: Interactive portfolio builder with live chat and portfolio visualization
  - Real-time conversation with the AI agent
  - Portfolio display with charts and tables
  - Responsive design for mobile and desktop

- **A2A Protocol Interface**: Standard agent-to-agent communication endpoint
  - `/message:send` endpoint for multi-turn conversations
  - Agent card at `/.well-known/agent-card.json`
  - Supports context management for stateful interactions

- **ADK Web UI**: Built-in Google ADK interface
  - Launch with `adk web portfolio_manager/`
  - Automatic session management
  - Debug console for agent outputs

#### 2. API Server Layer (FastAPI)
The FastAPI server provides three main endpoints:

- **`POST /api/generate-portfolio`**: Direct portfolio generation
  - Accepts JSON with user profile
  - Returns complete portfolio with all analysis outputs
  - Synchronous execution for immediate results

- **`POST /message:send`**: A2A protocol endpoint
  - Multi-turn conversation support
  - Context-aware session management
  - Returns Task objects with status and artifacts

- **`InMemoryRunner`**: ADK session manager
  - Maintains conversation state
  - Routes messages to root agent
  - Handles agent transfers

#### 3. Root Agent (LlmAgent)
The orchestrator agent that handles user interaction:

**Model**: `gemini-2.0-flash`

**Responsibilities**:
- Conducts conversational profile collection (Phase 1)
- Validates all required data points are collected
- Calculates risk score (1-10) from user inputs
- Transfers to analysis_pipeline when ready (Phase 2)
- Returns final report to user

**Profile Data Points**:
1. Investment capital (amount)
2. Investment goal (preserve_capital | income | balanced_growth | aggressive_growth)
3. Time horizon (<1yr | 1-3yr | 3-5yr | 5-10yr | 10+yr)
4. Risk tolerance (max acceptable loss: 5% - 50%)
5. Investment experience (none | beginner | intermediate | advanced | expert)
6. Income stability (very_unstable | unstable | stable | very_stable)

**Risk Score Calculation**:
```python
goal_scores = {
    "preserve_capital": 2,
    "income": 4,
    "balanced_growth": 6,
    "aggressive_growth": 8
}

risk_score = avg(goal_score, horizon_score, loss_score, experience_score)
# Result: 1-10 scale
# 1-2: Ultra Conservative
# 3-4: Conservative
# 5-6: Moderate
# 7-8: Growth
# 9-10: Aggressive
```

#### 4. Analysis Pipeline (SequentialAgent)
Container for 7 specialized sub-agents that run **sequentially** (not in parallel) to avoid API rate limits.

**Sequential Execution Rationale**:
- Alpha Vantage Free Tier: 5 API calls per minute
- Each agent makes 3-8 API calls
- Parallel execution would exceed rate limits
- Sequential pattern ensures reliability

#### 5. Tools & API Integration Layer
Python modules providing data access and calculations:

**stock_api.py** (Alpha Vantage):
- `get_stock_quote(symbol)` - Real-time price
- `get_company_fundamentals(symbol)` - P/E, revenue, margins
- `get_technical_indicators(symbol)` - RSI, MACD, SMA
- `get_historical_prices(symbol, period)` - Price history
- `get_sector_performance()` - Sector returns
- Built-in rate limiter with exponential backoff

**calculations.py** (Financial Math):
- `calculate_sharpe_ratio(returns)` - Risk-adjusted return
- `calculate_portfolio_volatility(weights, returns)` - Portfolio std dev
- `calculate_beta(stock_returns, market_returns)` - Systematic risk
- `calculate_max_drawdown(prices)` - Worst peak-to-trough decline
- `calculate_correlation_matrix(returns)` - Diversification analysis

**macro_data.py** (Economic Indicators):
- `get_economic_indicators()` - GDP, CPI, unemployment, Fed funds rate
- `get_recession_indicators()` - Yield curve, consumer confidence
- `calculate_market_outlook_score()` - Aggregate sentiment

#### 6. External Data Sources
- **Alpha Vantage API**: Primary data source for stocks and economic data
- **JSON Data Files**: 
  - `risk_profiles.json` - Allocation rules by risk level
  - `stock_universe.json` - Curated stock list by sector
  - `sector_correlations.json` - Historical sector performance correlations

---

## Conversation Flow

![Conversation Flow](docs/conversation_flow.svg)

### Phase 1: Profile Collection (Conversational)

The root agent conducts a natural, conversational interview to gather investor profile data. This phase uses the **LLM's natural language capabilities** to provide a human-like experience.

#### Example Conversation

```
🤖 Agent: Hello! I'm your AI Portfolio Manager. Let's create a 
          personalized investment portfolio. How much would you 
          like to invest?

👤 User: $10,000

🤖 Agent: Great! $10,000 is a solid starting point. Now, what's 
          your primary investment goal?
          1. Preserve capital (low risk)
          2. Generate regular income
          3. Balanced growth and income
          4. Aggressive growth
          5. Maximum growth (highest risk)

👤 User: Balanced growth

🤖 Agent: Good choice. What's your investment time horizon?
          1. Less than 1 year
          2. 1-3 years
          3. 3-5 years
          4. 5-10 years
          5. 10+ years

👤 User: 5-10 years

🤖 Agent: Excellent. With a 5-10 year horizon, you can weather 
          market volatility. What's the maximum loss you'd be 
          comfortable with in a bad year?

👤 User: 15%

🤖 Agent: What's your investment experience level?
          1. None - I'm completely new to investing
          2. Beginner - I've done some research
          3. Intermediate - I have a basic understanding
          4. Advanced - I actively manage investments
          5. Expert - I have professional experience

👤 User: Intermediate

🤖 Agent: Last question: How stable is your income?
          1. Very unstable - Freelance/variable income
          2. Unstable - Some income variability
          3. Stable - Steady paycheck
          4. Very stable - Secure job with guaranteed income

👤 User: Stable

🤖 Agent: Perfect! I've collected your complete profile:
          
          Your Risk Profile:
          • Capital: $10,000
          • Goal: Balanced Growth
          • Time Horizon: 5-10 years
          • Risk Tolerance: 15% max loss
          • Experience: Intermediate
          • Income Stability: Stable
          • Risk Score: 6/10 (Moderate)
          • Risk Category: Moderately Aggressive
          
          Ready to generate your personalized portfolio?

👤 User: Yes!
```

### Phase 2: Portfolio Generation (Automated Pipeline)

Once the user confirms, the root agent **transfers control** to the `analysis_pipeline` SequentialAgent, which orchestrates the 7 sub-agents.

**User Profile JSON** (passed to pipeline):
```json
{
  "user_profile": {
    "capital": 10000,
    "currency": "USD",
    "investment_goal": "balanced_growth",
    "time_horizon": "5_10_years",
    "time_horizon_years": 7.5,
    "risk_tolerance": "moderate",
    "max_loss_percent": 15,
    "investment_experience": "intermediate",
    "income_stability": "stable",
    "risk_score": 6,
    "risk_category": "Moderately Aggressive",
    "profile_summary": "Moderate risk investor with 5-10 year horizon seeking balanced growth."
  }
}
```

**Pipeline Execution**:
The analysis_pipeline runs 7 agents sequentially, with each agent's output becoming input for subsequent agents.

**Execution Time**: ~60-90 seconds (rate-limited by API)

---

## Sequential Pipeline

![Sequential Pipeline](docs/sequential_pipeline.svg)

### Agent 1: Macro Agent

**Purpose**: Analyze macroeconomic conditions to determine market outlook

**Tools Used**:
- `get_economic_indicators()` - Fetches GDP growth, CPI inflation, unemployment rate, Fed funds rate
- `get_recession_indicators()` - Optional yield curve, consumer confidence

**Analysis Framework**:
- **GDP Growth**: Strong (>3%) = cyclical sectors; Weak (<1%) = defensive sectors
- **Inflation**: Low (<2%) = growth stocks; High (>5%) = commodities, TIPS
- **Unemployment**: Low (<4%) = strong consumer spending
- **Interest Rates**: Rising = financials; Falling = growth stocks

**Output Schema**:
```json
{
  "macro_outlook": {
    "market_sentiment": "bullish",
    "confidence_score": 75,
    "economic_summary": {
      "gdp_assessment": "moderate",
      "inflation_assessment": "target",
      "employment_assessment": "healthy",
      "rate_environment": "neutral"
    },
    "economic_condition": "moderate_growth",
    "key_factors": [
      "GDP growing at 2.5% annually",
      "Inflation at 2.8% (near Fed target)",
      "Unemployment at 4.1% (near full employment)"
    ],
    "sector_implications": {
      "favored": ["Technology", "Healthcare", "Consumer Discretionary"],
      "avoid": ["Real Estate", "Utilities"]
    },
    "risk_factors": [
      "Potential interest rate volatility",
      "Geopolitical tensions"
    ],
    "recommendation": "Moderate bullish stance. Favor growth sectors with selective value plays."
  }
}
```

**Code Location**: `sub_agents/macro_agent.py`

---

### Agent 2: Sector Agent

**Purpose**: Select 3-5 optimal sectors based on macroeconomic outlook

**Input Dependencies**:
- `macro_outlook` (from Agent 1)
- `user_profile` (risk score)
- `sector_correlations.json` (historical data)

**Selection Criteria**:
1. Alignment with economic conditions (from macro_outlook)
2. Risk-adjusted returns matching user's risk profile
3. Low inter-sector correlation (diversification)
4. Historical performance in similar economic environments

**Sector Categories**:
- **Cyclical**: Technology, Consumer Discretionary, Industrials, Financials
- **Defensive**: Healthcare, Consumer Staples, Utilities
- **Sensitive**: Energy, Materials, Real Estate

**Output Schema**:
```json
{
  "top_sectors": {
    "sectors": [
      "Information Technology",
      "Healthcare",
      "Consumer Discretionary",
      "Industrials"
    ],
    "sector_weights": {
      "Information Technology": 35,
      "Healthcare": 25,
      "Consumer Discretionary": 20,
      "Industrials": 20
    },
    "rationale": "Technology favored in moderate growth, low-rate environment. Healthcare provides defensive balance. Consumer discretionary and industrials benefit from steady GDP growth.",
    "risk_assessment": "Moderate volatility portfolio with growth tilt",
    "diversification_score": 8.2
  }
}
```

**Code Location**: `sub_agents/sector_agent.py`

---

### Agent 3: Stock Selection Agent

**Purpose**: Pick 8-12 quality stocks from selected sectors using fundamental and technical analysis

**Input Dependencies**:
- `top_sectors` (from Agent 2)
- `user_profile` (risk score, capital)
- `stock_universe.json` (candidate stocks)

**Tools Used**:
- `get_stock_quote(symbol)` - Current price
- `get_company_fundamentals(symbol)` - P/E ratio, revenue growth, profit margins, debt/equity
- `get_technical_indicators(symbol)` - RSI (14), MACD, 50-day SMA, 200-day SMA

**Selection Criteria**:

**Fundamental Filters**:
- P/E Ratio: 10-40 (avoid extreme valuation)
- Revenue Growth: >5% annually
- Profit Margin: >10%
- Debt/Equity: <2.0 (manageable debt)
- Market Cap: >$2B (avoid micro-caps)

**Technical Filters**:
- RSI: 30-70 (not overbought/oversold)
- Price > 200-day SMA (long-term uptrend)
- Positive MACD crossover (momentum)

**Diversification Rules**:
- Max 3 stocks per sector
- Max 20% in any single position
- Min 8 stocks total (diversification)

**Output Schema**:
```json
{
  "selected_stocks": {
    "stocks": [
      {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Information Technology",
        "current_price": 150.25,
        "fundamentals": {
          "pe_ratio": 28.5,
          "revenue_growth": 12.3,
          "profit_margin": 25.2,
          "debt_equity": 1.5
        },
        "technicals": {
          "rsi": 62,
          "macd": "bullish",
          "price_vs_sma200": "above"
        },
        "quality_score": 8.7,
        "rationale": "Strong fundamentals, consistent revenue growth, bullish technicals"
      },
      {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "sector": "Information Technology",
        "current_price": 375.80,
        "fundamentals": {
          "pe_ratio": 32.1,
          "revenue_growth": 14.5,
          "profit_margin": 36.8,
          "debt_equity": 0.9
        },
        "technicals": {
          "rsi": 58,
          "macd": "bullish",
          "price_vs_sma200": "above"
        },
        "quality_score": 9.2,
        "rationale": "Market leader, high margins, strong balance sheet"
      },
      {
        "symbol": "UNH",
        "name": "UnitedHealth Group",
        "sector": "Healthcare",
        "current_price": 520.45,
        "quality_score": 8.5,
        "rationale": "Defensive healthcare leader, stable earnings"
      }
      // ... 9 more stocks
    ],
    "total_candidates_screened": 85,
    "stocks_passed_filters": 12,
    "sectors_represented": ["Technology", "Healthcare", "Consumer Discretionary", "Industrials"]
  }
}
```

**API Rate Limiting**:
This agent makes the most API calls (~12 calls for 12 stocks). The built-in rate limiter ensures we stay within the 5 calls/minute limit.

```python
# Rate limiter implementation
@_rate_limit
def get_stock_quote(symbol: str) -> dict:
    # ... API call logic
```

**Code Location**: `sub_agents/stock_selection_agent.py`

---

### Agent 4: Portfolio Construction Agent

**Purpose**: Allocate capital across selected stocks based on risk profile

**Input Dependencies**:
- `selected_stocks` (from Agent 3)
- `user_profile` (capital, risk_score)
- `risk_profiles.json` (allocation rules)

**Allocation Strategies by Risk Score**:

| Risk Score | Strategy | Max Position | Sector Concentration |
|------------|----------|--------------|---------------------|
| 1-2 | Ultra Conservative | 15% | 30% |
| 3-4 | Conservative | 18% | 35% |
| 5-6 | Moderate | 20% | 40% |
| 7-8 | Growth | 25% | 45% |
| 9-10 | Aggressive | 30% | 50% |

**Allocation Algorithm**:
1. Start with equal weights across all stocks
2. Adjust based on quality scores (higher quality = higher weight)
3. Apply sector weight constraints from Agent 2
4. Apply maximum position size limits
5. Calculate exact share quantities (must be whole numbers)
6. Minimize cash drag (unallocated capital)

**Output Schema**:
```json
{
  "portfolio": {
    "allocations": [
      {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Information Technology",
        "weight_percent": 18,
        "shares": 12,
        "price_per_share": 150.25,
        "total_value": 1803.00,
        "rationale": "High quality tech leader, 18% allocation within 20% max"
      },
      {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "sector": "Information Technology",
        "weight_percent": 15,
        "shares": 4,
        "price_per_share": 375.80,
        "total_value": 1503.20
      },
      {
        "symbol": "UNH",
        "name": "UnitedHealth Group",
        "sector": "Healthcare",
        "weight_percent": 12,
        "shares": 2,
        "price_per_share": 520.45,
        "total_value": 1040.90
      }
      // ... 9 more positions
    ],
    "portfolio_summary": {
      "total_invested": 9947.50,
      "cash_reserve": 52.50,
      "total_value": 10000.00,
      "num_positions": 12,
      "sector_breakdown": {
        "Information Technology": 33,
        "Healthcare": 24,
        "Consumer Discretionary": 21,
        "Industrials": 22
      },
      "largest_position_pct": 18,
      "smallest_position_pct": 6,
      "diversification_score": 8.5
    }
  }
}
```

**Code Location**: `sub_agents/portfolio_construction_agent.py`

---

### Agent 5: Performance Agent

**Purpose**: Calculate expected portfolio performance metrics

**Input Dependencies**:
- `portfolio` (from Agent 4)
- Historical price data for all stocks

**Tools Used**:
- `get_historical_prices(symbol, period="1y")` - Daily prices
- `calculate_sharpe_ratio(returns)` - Risk-adjusted return
- `calculate_portfolio_volatility(weights, returns)` - Standard deviation
- `calculate_beta(portfolio_returns, sp500_returns)` - Market risk
- `calculate_correlation_matrix(returns)` - Diversification

**Metrics Calculated**:

**Sharpe Ratio**:
```
Sharpe = (Portfolio Return - Risk-Free Rate) / Portfolio Volatility

Interpretation:
< 0: Bad (losing money)
0-1: Adequate
1-2: Good
2-3: Very Good
> 3: Excellent (verify data)
```

**Portfolio Volatility**:
```
Volatility = sqrt(sum(weight_i * weight_j * cov(return_i, return_j)))

Interpretation:
< 10%: Low volatility (conservative)
10-15%: Moderate volatility
15-20%: Elevated volatility (growth)
> 20%: High volatility (aggressive)
```

**Beta**:
```
Beta = Covariance(Portfolio, Market) / Variance(Market)

Interpretation:
< 0.8: Low market sensitivity (defensive)
0.8-1.2: Market-like behavior
> 1.2: High market sensitivity (aggressive)
```

**Output Schema**:
```json
{
  "performance_report": {
    "expected_annual_return": 12.5,
    "sharpe_ratio": 1.35,
    "sharpe_interpretation": "Good risk-adjusted return",
    "annualized_volatility": 15.2,
    "portfolio_beta": 1.02,
    "beta_interpretation": "Market-like risk profile",
    "max_drawdown": -18.3,
    "correlation_matrix": {
      "AAPL": {"MSFT": 0.72, "UNH": 0.35, ...},
      "MSFT": {"AAPL": 0.72, "UNH": 0.41, ...}
    },
    "sector_volatility": {
      "Information Technology": 18.5,
      "Healthcare": 12.3,
      "Consumer Discretionary": 16.7,
      "Industrials": 14.2
    },
    "risk_assessment": "Moderate volatility portfolio with market-like systematic risk. Sharpe ratio indicates good risk-adjusted returns.",
    "alignment_with_profile": true,
    "alignment_notes": "Volatility of 15.2% is within user's 15% max loss tolerance. Risk profile matches 6/10 moderate score."
  }
}
```

**Code Location**: `sub_agents/performance_agent.py`

---

### Agent 6: Backtest Agent

**Purpose**: Validate portfolio strategy using historical data

**Input Dependencies**:
- `portfolio` (from Agent 4)
- `performance_report` (from Agent 5)
- Historical prices (12 months)

**Tools Used**:
- `get_historical_prices(symbol, period="1y")` - Daily closing prices
- `calculate_portfolio_return(prices, weights)` - Time-series returns

**Backtesting Methodology**:
1. **Time Period**: Exactly 12 months prior to current date
2. **Simulation**: Assume portfolio was built 12 months ago with same allocations
3. **Rebalancing**: No rebalancing (buy-and-hold strategy)
4. **Benchmark**: Compare against S&P 500 ETF (SPY)
5. **Metrics**: Total return, max drawdown, win rate, Sharpe ratio

**Validation Criteria**:
- ✅ **PASS**: Return within expected range (±5%), max drawdown within risk tolerance
- ⚠️ **WARNING**: Return below expected but drawdown acceptable
- ❌ **FAIL**: Max drawdown exceeds user's risk tolerance

**Output Schema**:
```json
{
  "backtest_results": {
    "backtest_period": {
      "start_date": "2025-02-25",
      "end_date": "2026-02-25",
      "num_trading_days": 252
    },
    "portfolio_performance": {
      "total_return": 14.2,
      "annualized_return": 14.2,
      "max_drawdown": -8.3,
      "win_rate": 66.7,
      "sharpe_ratio": 1.42,
      "winning_months": 8,
      "losing_months": 4
    },
    "benchmark_performance": {
      "benchmark": "S&P 500 (SPY)",
      "total_return": 11.8,
      "max_drawdown": -10.5,
      "sharpe_ratio": 1.22
    },
    "comparison": {
      "excess_return": 2.4,
      "tracking_error": 3.5,
      "information_ratio": 0.69,
      "alpha": 2.1,
      "win_vs_benchmark": true
    },
    "monthly_returns": [
      {"month": "2025-03", "return": 2.3},
      {"month": "2025-04", "return": -1.5},
      {"month": "2025-05", "return": 3.1},
      // ... 9 more months
    ],
    "validation_status": "PASSED",
    "validation_notes": "Portfolio outperformed S&P 500 by 2.4%. Max drawdown of -8.3% is well within the user's 15% risk tolerance. Sharpe ratio of 1.42 indicates good risk-adjusted returns.",
    "risk_alignment": true,
    "risk_notes": "Portfolio behaved within expected risk parameters during backtest period."
  }
}
```

**Limitations**:
- **Survivorship Bias**: Only tests stocks that exist today
- **Look-Ahead Bias**: Portfolio constructed with current knowledge
- **Market Regime**: Past 12 months may not represent future conditions
- **Overfitting**: Strategy not validated on out-of-sample data

**Code Location**: `sub_agents/backtest_agent.py`

---

### Agent 7: Report Synthesizer Agent

**Purpose**: Generate comprehensive markdown investment report for the user

**Input Dependencies**:
- ALL outputs from Agents 1-6
- `user_profile`

**Report Sections**:

1. **Executive Summary**
   - Portfolio snapshot (total value, # stocks, risk level)
   - Expected return and risk metrics
   - Investment recommendation

2. **Your Investment Profile**
   - Capital, goals, time horizon
   - Risk tolerance and experience
   - Risk score and category

3. **Market Outlook**
   - Economic conditions summary
   - Favored sectors and rationale
   - Key risk factors

4. **Portfolio Composition**
   - Table with all stock positions
   - Sector breakdown pie chart
   - Allocation percentages

5. **Stock Analysis**
   - Detailed fundamentals for each stock
   - Technical indicators
   - Rationale for inclusion

6. **Risk & Performance Metrics**
   - Expected return
   - Sharpe ratio
   - Volatility
   - Beta
   - Max drawdown

7. **Historical Backtest**
   - 12-month performance
   - Comparison to S&P 500
   - Monthly returns chart
   - Validation status

8. **Investment Recommendations**
   - Rebalancing guidance
   - When to review portfolio
   - Risk management tips

9. **Disclaimers**
   - Not financial advice
   - Past performance ≠ future results
   - Consult professional advisor

**Output Schema**:
```json
{
  "final_report": "# Investment Portfolio Report\n\n## Executive Summary\n\n**Portfolio Value**: $10,000\n**Number of Stocks**: 12\n**Risk Level**: Moderate (6/10)\n**Expected Annual Return**: 12.5%\n**Sharpe Ratio**: 1.35 (Good)\n**Volatility**: 15.2%\n\n... (full markdown report)"
}
```

**Example Report** (abbreviated):
```markdown
# Investment Portfolio Report
Generated: 2026-02-25

## Executive Summary

Congratulations! Your personalized portfolio has been constructed and validated. 
Based on your moderate risk profile (6/10), we've created a balanced portfolio 
of 12 quality stocks across 4 sectors, designed to achieve your goal of 
balanced growth over a 5-10 year horizon.

**Portfolio Snapshot**:
- Total Investment: $10,000
- Number of Positions: 12 stocks
- Sectors: Technology (33%), Healthcare (24%), Consumer Discretionary (21%), Industrials (22%)
- Expected Annual Return: 12.5%
- Risk Level: Moderate (Volatility: 15.2%)
- Sharpe Ratio: 1.35 (Good risk-adjusted return)

**Backtest Results**:
✅ PASSED - Portfolio returned 14.2% over the past 12 months, outperforming 
the S&P 500 (11.8%). Maximum drawdown of -8.3% is well within your 15% 
risk tolerance.

---

## Your Investment Profile

| Attribute | Value |
|-----------|-------|
| Capital | $10,000 |
| Investment Goal | Balanced Growth |
| Time Horizon | 5-10 years |
| Risk Tolerance | 15% maximum loss |
| Experience Level | Intermediate |
| Income Stability | Stable |
| **Risk Score** | **6/10 (Moderate)** |

---

## Market Outlook

**Economic Conditions**: Moderate Growth Environment
- GDP growing at 2.5% annually (healthy expansion)
- Inflation at 2.8% (near Fed's 2% target)
- Unemployment at 4.1% (near full employment)
- Fed Funds Rate: 4.75% (neutral stance)

**Market Sentiment**: Bullish (Confidence: 75%)

**Favored Sectors**:
1. **Technology** - Benefits from innovation and low interest rates
2. **Healthcare** - Defensive sector with aging demographics
3. **Consumer Discretionary** - Strong consumer spending in growing economy
4. **Industrials** - Infrastructure spending and GDP growth

**Risk Factors**:
- Potential interest rate volatility
- Geopolitical tensions

---

## Portfolio Composition

| Stock | Sector | Allocation | Shares | Value |
|-------|--------|------------|--------|-------|
| AAPL | Technology | 18% | 12 | $1,803 |
| MSFT | Technology | 15% | 4 | $1,503 |
| UNH | Healthcare | 12% | 2 | $1,041 |
| HD | Consumer Disc | 10% | 4 | $1,000 |
| ... | ... | ... | ... | ... |

**Sector Breakdown**:
- Information Technology: 33%
- Healthcare: 24%
- Consumer Discretionary: 21%
- Industrials: 22%

---

## Stock Analysis

### Apple Inc. (AAPL) - 18% Allocation
**Sector**: Information Technology  
**Price**: $150.25  
**Shares**: 12 ($1,803 total)

**Fundamentals**:
- P/E Ratio: 28.5
- Revenue Growth: 12.3% annually
- Profit Margin: 25.2%
- Debt/Equity: 1.5

**Technicals**:
- RSI: 62 (neutral)
- MACD: Bullish crossover
- Price above 200-day SMA (uptrend)

**Investment Thesis**: Apple is a high-quality technology leader with 
consistent revenue growth, strong profitability, and a solid balance sheet. 
The company benefits from its ecosystem (iPhone, Mac, Services) and has 
demonstrated resilience across market cycles. Bullish technical indicators 
suggest continued momentum.

[... 11 more stock analyses ...]

---

## Risk & Performance Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Expected Annual Return | 12.5% | Above S&P 500 historical average (10%) |
| Sharpe Ratio | 1.35 | Good risk-adjusted return |
| Annualized Volatility | 15.2% | Moderate (within your 15% tolerance) |
| Portfolio Beta | 1.02 | Market-like risk |
| Max Expected Drawdown | -18.3% | Slightly above tolerance (monitor) |

**Risk Assessment**: Your portfolio has moderate volatility (15.2%) which 
aligns with your risk score of 6/10. The Sharpe ratio of 1.35 indicates you're 
being adequately compensated for the risk taken. Beta of 1.02 means your 
portfolio will move roughly in line with the overall market.

**Diversification**: The portfolio is well-diversified across 12 stocks and 
4 sectors. The correlation matrix shows low correlation between sectors 
(Technology vs Healthcare: 0.35), which reduces overall portfolio risk.

---

## Historical Backtest (12 Months)

**Period**: February 25, 2025 - February 25, 2026

| Metric | Portfolio | S&P 500 | Difference |
|--------|-----------|---------|------------|
| Total Return | 14.2% | 11.8% | +2.4% |
| Max Drawdown | -8.3% | -10.5% | +2.2% |
| Sharpe Ratio | 1.42 | 1.22 | +0.20 |
| Winning Months | 8/12 (67%) | 7/12 (58%) | +9% |

✅ **Validation: PASSED**

Your portfolio outperformed the S&P 500 by 2.4% with lower drawdown (-8.3% 
vs -10.5%). This validates the stock selection and allocation strategy. 
The maximum drawdown of -8.3% is well within your 15% risk tolerance.

**Monthly Performance**:
- Best Month: +3.7% (July 2025)
- Worst Month: -2.1% (September 2025)
- Winning Months: 8 out of 12

---

## Investment Recommendations

### Execution Plan
1. **Place Orders**: Execute all 12 stock purchases via your brokerage
2. **Order Type**: Use limit orders to avoid overpaying
3. **Timing**: Consider dollar-cost averaging over 2-3 weeks

### Portfolio Management
- **Rebalancing**: Review quarterly, rebalance if any position drifts >5% from target
- **Performance Review**: Check monthly, but avoid overreacting to short-term volatility
- **Tax Optimization**: Hold >1 year for long-term capital gains tax treatment

### Risk Management
- **Stop Loss**: Consider 20% stop loss per position for risk control
- **Position Size**: Never let one position exceed 25% due to appreciation
- **Emergency Fund**: Ensure 3-6 months expenses in cash before investing

### When to Sell
- Fundamental deterioration (earnings miss, margin compression)
- Sector rotation (economic conditions shift away from your sectors)
- Better opportunities emerge (reallocate to higher-conviction ideas)
- Rebalancing (take profits from winners, add to losers)

---

## Disclaimers

⚠️ **Important**: This portfolio is generated using AI-driven analysis and 
historical data. It is **NOT** personalized financial advice. Please note:

- Past performance does NOT guarantee future results
- All investments carry risk, including loss of principal
- Backtesting uses historical data and may not reflect future conditions
- Economic conditions and company fundamentals can change rapidly
- This system cannot predict black swan events or market crashes

**Recommendation**: Consult with a licensed financial advisor before making 
investment decisions. Consider your complete financial situation, including 
taxes, estate planning, and insurance needs.

---

## Next Steps

1. **Review**: Carefully review this report and all stock analyses
2. **Research**: Do your own due diligence on recommended stocks
3. **Consult**: Speak with a financial advisor if needed
4. **Execute**: Place orders through your brokerage account
5. **Monitor**: Track portfolio performance monthly

**Questions?** The AI agent is available for follow-up questions about this portfolio.

---

*Report generated by Automated Portfolio Manager v2.0.0*  
*Powered by Google ADK (gemini-2.0-flash)*  
*Data source: Alpha Vantage API*
```

**Code Location**: `sub_agents/report_synthesizer_agent.py`

---

## Tools & APIs

### Stock API (`tools/stock_api.py`)

Wrapper for Alpha Vantage API with rate limiting.

**Rate Limiter Implementation**:
```python
RATE_LIMIT_CALLS = 5  # Max calls per period
RATE_LIMIT_PERIOD = 60  # seconds
_call_timestamps: list[float] = []

def _rate_limit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _call_timestamps
        now = time.time()
        
        # Remove old timestamps
        _call_timestamps = [ts for ts in _call_timestamps 
                           if now - ts < RATE_LIMIT_PERIOD]
        
        # Check if limit exceeded
        if len(_call_timestamps) >= RATE_LIMIT_CALLS:
            # Wait until oldest call expires
            sleep_time = RATE_LIMIT_PERIOD - (now - _call_timestamps[0]) + 1
            if sleep_time > 0:
                time.sleep(sleep_time)
                _call_timestamps = []
        
        # Record this call
        _call_timestamps.append(time.time())
        return func(*args, **kwargs)
    
    return wrapper
```

**Functions**:

#### `get_stock_quote(symbol: str) -> dict`
Fetches real-time stock price data.

**API Endpoint**: `TIME_SERIES_INTRADAY`

**Returns**:
```python
{
    "symbol": "AAPL",
    "price": 150.25,
    "change": 2.35,
    "change_percent": 1.59,
    "volume": 54328190,
    "previous_close": 147.90,
    "timestamp": "2026-02-25 15:30:00"
}
```

#### `get_company_fundamentals(symbol: str) -> dict`
Fetches company financial metrics.

**API Endpoint**: `OVERVIEW`

**Returns**:
```python
{
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "market_cap": 2450000000000,  # $2.45T
    "pe_ratio": 28.5,
    "peg_ratio": 2.1,
    "eps": 5.26,
    "revenue_per_share": 23.45,
    "profit_margin": 0.252,
    "revenue_growth_yoy": 0.123,
    "debt_to_equity": 1.5,
    "dividend_yield": 0.005
}
```

#### `get_technical_indicators(symbol: str) -> dict`
Fetches technical analysis indicators.

**API Endpoints**: `RSI`, `MACD`, `SMA`

**Returns**:
```python
{
    "symbol": "AAPL",
    "rsi_14": 62,  # 0-100 scale
    "macd": {
        "macd": 2.35,
        "signal": 1.89,
        "histogram": 0.46,
        "crossover": "bullish"  # or "bearish"
    },
    "sma_50": 145.20,
    "sma_200": 138.50,
    "price_vs_sma50": "above",
    "price_vs_sma200": "above"
}
```

#### `get_historical_prices(symbol: str, period: str = "1y") -> list`
Fetches historical daily closing prices.

**API Endpoint**: `TIME_SERIES_DAILY_ADJUSTED`

**Returns**:
```python
[
    {"date": "2025-02-25", "close": 150.25, "volume": 54328190},
    {"date": "2025-02-24", "close": 147.90, "volume": 48935210},
    # ... 250 more days
]
```

---

### Calculations (`tools/calculations.py`)

Financial mathematics library for portfolio analysis.

#### `calculate_sharpe_ratio(returns: list, risk_free_rate: float = 0.05) -> dict`

**Formula**:
```
Sharpe Ratio = (Mean Return - Risk-Free Rate) / Standard Deviation of Returns
```

**Returns**:
```python
{
    "sharpe_ratio": 1.35,
    "annualized_return": 0.125,
    "annualized_volatility": 0.152,
    "interpretation": "Good risk-adjusted return"
}
```

#### `calculate_portfolio_volatility(weights: list, returns: list) -> float`

**Formula**:
```
σ_p = sqrt(Σ Σ w_i * w_j * σ_i * σ_j * ρ_ij)

Where:
- w_i, w_j = portfolio weights
- σ_i, σ_j = asset standard deviations
- ρ_ij = correlation between assets i and j
```

**Returns**: `0.152` (15.2% annualized volatility)

#### `calculate_beta(stock_returns: list, market_returns: list) -> float`

**Formula**:
```
β = Covariance(Stock, Market) / Variance(Market)
```

**Returns**: `1.02` (stock moves 1.02x the market)

#### `calculate_max_drawdown(prices: list) -> dict`

**Formula**:
```
Max Drawdown = (Trough - Peak) / Peak

Where:
- Peak = highest portfolio value
- Trough = lowest subsequent value
```

**Returns**:
```python
{
    "max_drawdown": -0.183,  # -18.3%
    "peak_date": "2025-07-15",
    "trough_date": "2025-09-20",
    "recovery_date": "2025-11-10",
    "days_to_recover": 52
}
```

---

### Macro Data (`tools/macro_data.py`)

Economic indicators fetching module.

#### `get_economic_indicators() -> dict`

Fetches key macroeconomic metrics.

**API Endpoints** (Alpha Vantage):
- `REAL_GDP` - GDP growth rate
- `CPI` - Consumer Price Index (inflation)
- `UNEMPLOYMENT` - Unemployment rate
- `FEDERAL_FUNDS_RATE` - Fed interest rate

**Returns**:
```python
{
    "gdp": {
        "value": 2.5,
        "unit": "percent",
        "period": "2025-Q4",
        "assessment": "moderate"
    },
    "inflation": {
        "value": 2.8,
        "unit": "percent",
        "period": "2026-01",
        "assessment": "target"
    },
    "unemployment": {
        "value": 4.1,
        "unit": "percent",
        "period": "2026-01",
        "assessment": "healthy"
    },
    "interest_rate": {
        "value": 4.75,
        "unit": "percent",
        "period": "2026-02",
        "assessment": "neutral"
    }
}
```

#### `calculate_market_outlook_score(indicators: dict) -> float`

Generates an aggregate market sentiment score (0-100).

**Algorithm**:
- GDP growth: 0-30 points (higher = more points)
- Inflation: 0-25 points (closer to 2% = more points)
- Unemployment: 0-25 points (lower = more points)
- Interest rates: 0-20 points (accommodative = more points)

**Returns**: `75` (bullish score: 70-80 = bullish, 50-70 = neutral, <50 = bearish)

---

## Data Sources

### Alpha Vantage API

**Website**: https://www.alphavantage.co/

**Free Tier Limits**:
- 5 API calls per minute
- 500 API calls per day
- No credit card required

**Data Coverage**:
- Real-time stock quotes (15-minute delay)
- Company fundamentals (updated quarterly)
- Technical indicators (calculated on-demand)
- Economic indicators (monthly/quarterly updates)
- Historical prices (up to 20 years)

**Reliability**:
- 99.9% uptime SLA (paid tiers)
- Data sourced from major exchanges (NYSE, NASDAQ)
- Economic data from US Federal Reserve (FRED)

**Rate Limiting Strategy**:
To stay within the 5 calls/minute limit, the system uses:
1. **Sliding window rate limiter** in `stock_api.py`
2. **Sequential agent execution** (no parallelization)
3. **Caching** of frequently accessed data (fundamentals)
4. **Exponential backoff** on rate limit errors

**Alternative Data Sources** (for premium deployments):
- **Yahoo Finance** (via yfinance) - Free but less reliable
- **IEX Cloud** - Paid tier with higher limits
- **Polygon.io** - Real-time data with generous free tier
- **Financial Modeling Prep** - Comprehensive fundamental data

### JSON Data Files

Located in `portfolio_manager/data/`:

#### `risk_profiles.json`
Allocation rules by risk score (1-10).

```json
{
  "1": {
    "category": "Ultra Conservative",
    "max_position_pct": 15,
    "max_sector_pct": 30,
    "min_positions": 10,
    "cash_reserve_pct": 10,
    "sector_allocations": {
      "Consumer Staples": 30,
      "Utilities": 25,
      "Healthcare": 20,
      "Bonds": 25
    }
  },
  "6": {
    "category": "Moderate",
    "max_position_pct": 20,
    "max_sector_pct": 40,
    "min_positions": 8,
    "cash_reserve_pct": 2,
    "sector_allocations": {
      "Technology": 30,
      "Healthcare": 25,
      "Consumer Discretionary": 20,
      "Industrials": 15,
      "Financials": 10
    }
  }
}
```

#### `stock_universe.json`
Curated list of quality stocks per sector.

```json
{
  "Information Technology": {
    "stocks": [
      {"symbol": "AAPL", "name": "Apple Inc.", "market_cap": "large"},
      {"symbol": "MSFT", "name": "Microsoft Corporation", "market_cap": "large"},
      {"symbol": "NVDA", "name": "NVIDIA Corporation", "market_cap": "large"}
    ]
  },
  "Healthcare": {
    "stocks": [
      {"symbol": "UNH", "name": "UnitedHealth Group", "market_cap": "large"},
      {"symbol": "JNJ", "name": "Johnson & Johnson", "market_cap": "large"}
    ]
  }
}
```

#### `sector_correlations.json`
Historical correlation matrix between sectors.

```json
{
  "correlations": {
    "Technology": {
      "Technology": 1.00,
      "Healthcare": 0.35,
      "Consumer Discretionary": 0.62,
      "Utilities": -0.12
    },
    "Healthcare": {
      "Technology": 0.35,
      "Healthcare": 1.00,
      "Consumer Staples": 0.54
    }
  },
  "volatilities": {
    "Technology": 0.22,
    "Healthcare": 0.15,
    "Utilities": 0.12
  }
}
```

---

## API Rate Limiting

### Problem Statement

Alpha Vantage Free Tier allows only **5 API calls per minute** and **500 calls per day**. A typical portfolio generation requires:

- Macro Agent: 4 API calls (GDP, CPI, unemployment, rates)
- Stock Selection Agent: 12 API calls (1 per stock candidate)
- Performance Agent: 12 API calls (historical prices for each stock)
- Backtest Agent: 12 API calls (historical prices again for validation)

**Total**: ~40 API calls per portfolio

### Solution: Sequential Execution

The system uses a **SequentialAgent** instead of **ParallelAgent** to ensure agents run one at a time, preventing rate limit violations.

```python
# portfolio_manager/agent.py
analysis_pipeline = SequentialAgent(
    name="analysis_pipeline",
    sub_agents=[
        macro_agent,              # Waits for completion
        sector_agent,             # Then starts
        stock_selection_agent,    # Then starts
        portfolio_construction_agent,
        performance_agent,
        backtest_agent,
        report_synthesizer_agent
    ]
)
```

### Rate Limiter Implementation

```python
# tools/stock_api.py
RATE_LIMIT_CALLS = 5
RATE_LIMIT_PERIOD = 60  # seconds
_call_timestamps: list[float] = []

@_rate_limit
def get_stock_quote(symbol: str) -> dict:
    """
    Decorated with @_rate_limit.
    If 5 calls made in last 60 seconds, sleeps until oldest call expires.
    """
    # ... API call logic
```

### Execution Timeline

```
Time (s) | Agent            | API Calls | Cumulative | Status
---------|------------------|-----------|------------|--------
0        | Macro Agent      | 4         | 4          | ✅
12       | Sector Agent     | 0         | 4          | ✅
12       | Stock Selection  | 1         | 5          | ✅ (5th call)
24       | Stock Selection  | 1         | 4*         | ⏸ Wait 36s (rate limit)
60       | Stock Selection  | 1         | 5          | ✅ (window reset)
300      | Report Agent     | 0         | 0          | ✅

* After 60s from first call, window resets
```

**Total Execution Time**: ~60-90 seconds (rate-limited)

### Caching Strategy

To reduce API calls, the system caches:
- Company fundamentals (24-hour TTL)
- Economic indicators (24-hour TTL)
- Historical prices (1-hour TTL)

```python
# Cached fundamentals stored in data/cached_fundamentals.json
{
  "AAPL": {
    "data": {...},
    "timestamp": "2026-02-25T10:30:00Z",
    "ttl": 86400
  }
}
```

---

## Agent-to-Agent (A2A) Protocol

The portfolio manager implements the **A2A Protocol** for interoperability with other AI agents.

### Agent Card

**Endpoint**: `GET /.well-known/agent-card.json`

```json
{
  "name": "Portfolio Manager",
  "description": "Autonomous AI agent for personalized investment portfolio creation and analysis.",
  "version": "2.0.0",
  "supportedInterfaces": [
    {
      "url": "/message:send",
      "protocolBinding": "HTTP+JSON",
      "protocolVersion": "0.3"
    }
  ],
  "provider": {
    "organization": "Drayvn",
    "url": "https://drayvn.ai"
  },
  "capabilities": {
    "streaming": false,
    "pushNotifications": false,
    "extensions": []
  },
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["application/json", "text/markdown"]
}
```

### Message Sending

**Endpoint**: `POST /message:send`

**Request**:
```json
{
  "message": {
    "messageId": "msg_12345",
    "role": "ROLE_USER",
    "parts": [
      {
        "text": "I want to invest $10,000 with moderate risk"
      }
    ],
    "contextId": "conv_67890",
    "created": "2026-02-25T10:30:00Z"
  },
  "contextId": "conv_67890"
}
```

**Response**:
```json
{
  "task": {
    "id": "task_abc123",
    "contextId": "conv_67890",
    "status": {
      "state": "input_required",
      "message": {
        "messageId": "msg_54321",
        "role": "ROLE_AGENT",
        "parts": [
          {
            "text": "Great! $10,000 is a solid starting point. What's your primary investment goal? 1. Preserve capital 2. Generate income 3. Balanced growth ..."
          }
        ],
        "contextId": "conv_67890",
        "taskId": "task_abc123",
        "created": "2026-02-25T10:30:05Z"
      },
      "timestamp": "2026-02-25T10:30:05Z"
    }
  }
}
```

### Conversation Flow

```
User → A2A Client → Portfolio Manager A2A Endpoint
                    ↓
            InMemoryRunner (maintains session)
                    ↓
            Root Agent (profile collection)
                    ↓
            Analysis Pipeline (portfolio generation)
                    ↓
                 Response → A2A Client → User
```

### Code Implementation

```python
# server.py
_a2a_runners: Dict[str, InMemoryRunner] = {}
_a2a_sessions: Dict[str, Any] = {}

@app.post("/message:send", response_model=Dict[str, Any])
async def a2a_send_message(request: SendMessageRequest):
    # Use contextId to maintain conversation state
    context_id = request.contextId or str(uuid.uuid4())
    
    # Get or create runner and session
    if context_id not in _a2a_runners:
        runner = InMemoryRunner(agent=root_agent, app_name="portfolio_manager")
        _a2a_runners[context_id] = runner
        session = await runner.session_service.create_session(...)
        _a2a_sessions[context_id] = session
    
    runner = _a2a_runners[context_id]
    session = _a2a_sessions[context_id]
    
    # Extract user text and create ADK message
    user_text = request.message.parts[0].text
    adk_message = genai_types.Content(role="user", parts=[...])
    
    # Run agent turn
    agent_response_text = ""
    async for event in runner.run_async(...):
        if event.content and event.content.parts:
            agent_response_text += event.content.parts[0].text
    
    # Construct Task object with status
    task = Task(
        id=str(uuid.uuid4()),
        contextId=context_id,
        status=TaskStatus(
            state="completed" if is_complete else "input_required",
            message=Message(...)
        )
    )
    
    return {"task": task.dict()}
```

---

## Deployment Guide

### Prerequisites

- Python 3.10+
- Google API Key (Gemini)
- Alpha Vantage API Key (free)

### Local Development

```bash
# 1. Clone repository
cd portfolio_manager

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run with ADK Web UI
adk web portfolio_manager/

# OR run with FastAPI
uvicorn portfolio_manager.server:app --reload --port 8001
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "portfolio_manager.server:app", "--host", "0.0.0.0", "--port", "8001"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  portfolio_manager:
    build: .
    ports:
      - "8001:8001"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
      - GEMINI_MODEL=gemini-2.0-flash
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

```bash
# Deploy with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Considerations

#### 1. Database Integration
Replace InMemoryRunner with persistent storage:

```python
# Use PostgreSQL for session storage
from google.adk.sessions import DatabaseSessionService

session_service = DatabaseSessionService(
    connection_string="postgresql://user:pass@localhost/portfolio_manager"
)

runner = Runner(
    agent=root_agent,
    app_name="portfolio_manager",
    session_service=session_service
)
```

#### 2. API Key Management
Use secrets management:

```python
# AWS Secrets Manager example
import boto3

def get_api_keys():
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId='portfolio_manager/api_keys')
    return json.loads(secret['SecretString'])

keys = get_api_keys()
GOOGLE_API_KEY = keys['google_api_key']
ALPHA_VANTAGE_API_KEY = keys['alpha_vantage_api_key']
```

#### 3. Caching Layer
Add Redis for API response caching:

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cached_api_call(symbol: str, endpoint: str, ttl: int = 3600):
    cache_key = f"{endpoint}:{symbol}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Make API call
    data = make_alpha_vantage_request(endpoint, symbol)
    redis_client.setex(cache_key, ttl, json.dumps(data))
    
    return data
```

#### 4. Monitoring & Logging

```python
# Structured logging
import logging
import structlog

logger = structlog.get_logger()

@app.post("/api/generate-portfolio")
async def generate_portfolio(request: PortfolioRequest):
    logger.info("portfolio_generation_started", capital=request.capital, risk_score=risk_data['risk_score'])
    
    try:
        result = await run_autonomous_agent(profile)
        logger.info("portfolio_generation_completed", num_stocks=len(result['parsed']['portfolio']['allocations']))
        return result
    except Exception as e:
        logger.error("portfolio_generation_failed", error=str(e))
        raise
```

#### 5. Rate Limiting (Server-Side)

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/api/generate-portfolio", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def generate_portfolio(request: PortfolioRequest):
    # Limit to 10 portfolio generations per minute per user
    ...
```

---

## Testing & Validation

### Unit Tests

```python
# tests/test_calculations.py
import pytest
from tools.calculations import calculate_sharpe_ratio

def test_sharpe_ratio_positive_returns():
    returns = [0.01, 0.02, 0.015, 0.018, 0.012]
    result = calculate_sharpe_ratio(returns, risk_free_rate=0.05)
    
    assert result['sharpe_ratio'] > 0
    assert result['annualized_return'] > 0.05
    assert result['interpretation'] in ['adequate', 'good', 'very_good']

def test_sharpe_ratio_negative_returns():
    returns = [-0.01, -0.02, -0.015]
    result = calculate_sharpe_ratio(returns, risk_free_rate=0.05)
    
    assert result['sharpe_ratio'] < 0
    assert result['interpretation'] == 'bad'
```

```bash
# Run tests
pytest portfolio_manager/tests/ -v

# With coverage
pytest portfolio_manager/tests/ --cov=portfolio_manager --cov-report=html
```

### Integration Tests

```python
# tests/test_stock_api.py
import pytest
from tools.stock_api import get_stock_quote

def test_get_stock_quote_valid_symbol():
    result = get_stock_quote("AAPL")
    
    assert result['symbol'] == "AAPL"
    assert result['price'] > 0
    assert result['volume'] > 0

def test_get_stock_quote_invalid_symbol():
    result = get_stock_quote("INVALID")
    
    assert 'error' in result
```

### End-to-End Test

```python
# tests/test_pipeline.py
import pytest
from agent import root_agent
from google.adk.runners import Runner

@pytest.mark.asyncio
async def test_portfolio_generation_flow():
    runner = Runner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(...)
    
    # Simulate profile collection
    profile_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part.from_text(text='{"user_profile": {...}}')]
    )
    
    responses = []
    async for event in runner.run_async(session_id=session.id, new_message=profile_message):
        if event.content:
            responses.append(event.content.parts[0].text)
    
    full_response = "\n".join(responses)
    
    # Assertions
    assert "portfolio" in full_response.lower()
    assert "macro_outlook" in full_response
    assert "selected_stocks" in full_response
    assert "backtest_results" in full_response
```

### Validation Checklist

Before production deployment:

- [ ] Unit tests pass (100% critical path coverage)
- [ ] Integration tests pass (API calls work)
- [ ] End-to-end test completes portfolio generation
- [ ] Rate limiter prevents API quota violations
- [ ] Invalid inputs handled gracefully
- [ ] Error messages are user-friendly
- [ ] Logging captures all critical events
- [ ] Performance metrics (response time < 120s)
- [ ] Security review (no API key leaks)
- [ ] Documentation is up-to-date

---

## Troubleshooting

### Common Issues

#### 1. API Rate Limit Exceeded

**Error**: `Rate limit exceeded: Please visit https://www.alphavantage.co/premium/ ...`

**Cause**: Made more than 5 API calls in 60 seconds.

**Solution**:
- Verify `SequentialAgent` is used (not Parallel)
- Check rate limiter is enabled in `stock_api.py`
- Add delays between agent executions

```python
# Add explicit delay if needed
import time
time.sleep(15)  # Wait 15 seconds between agents
```

#### 2. Google API Key Invalid

**Error**: `google.genai.types.GoogleAPIError: Invalid API key`

**Cause**: Missing or incorrect `GOOGLE_API_KEY` in environment.

**Solution**:
```bash
# Verify .env file
cat .env | grep GOOGLE_API_KEY

# Test API key manually
curl -X POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_KEY \
  -H 'Content-Type: application/json' \
  -d '{"contents": [{"parts": [{"text": "test"}]}]}'
```

#### 3. Stock Not Found

**Error**: `Error fetching quote for XYZ: Invalid API call`

**Cause**: Stock symbol doesn't exist or is delisted.

**Solution**:
- Verify symbol on [Yahoo Finance](https://finance.yahoo.com/)
- Update `stock_universe.json` to remove invalid symbols
- Add validation in stock selection agent

```python
# Add validation
def validate_symbol(symbol: str) -> bool:
    result = get_stock_quote(symbol)
    return 'error' not in result
```

#### 4. Agent Doesn't Transfer to Pipeline

**Error**: Portfolio generation hangs after profile collection.

**Cause**: Root agent doesn't recognize completion signal.

**Solution**:
- Verify user confirms ("Yes" or "Proceed")
- Check root agent's transfer logic
- Review prompt engineering in `ROOT_AGENT_INSTRUCTION`

```python
# Debug transfer
if "ready" in user_message.lower() or "yes" in user_message.lower():
    logger.info("Transferring to analysis_pipeline")
    # Transfer logic
````

#### 5. Backtest Returns Unrealistic Results

**Error**: Backtest shows 300% return in 12 months.

**Cause**: Data quality issue or calculation bug.

**Solution**:
- Verify historical prices are correct
- Check for stock splits (adjust prices)
- Validate date range (exactly 12 months)

```python
# Add sanity checks
if backtest_return > 1.0:  # 100%
    logger.warning("Unrealistic backtest return", return=backtest_return)
    # Flag for manual review
```

#### 6. Memory Leak (Long-Running Server)

**Symptom**: Server memory usage grows over time.

**Cause**: InMemoryRunner accumulates sessions.

**Solution**:
```python
# Implement session cleanup
import asyncio

async def cleanup_old_sessions():
    while True:
        await asyncio.sleep(3600)  # Every hour
        current_time = time.time()
        for context_id, session in list(_a2a_sessions.items()):
            if current_time - session.created_at > 86400:  # 24 hours
                del _a2a_runners[context_id]
                del _a2a_sessions[context_id]
                logger.info("Cleaned up session", context_id=context_id)

# Start cleanup task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_old_sessions())
```

### Debug Mode

Enable verbose logging:

```python
# server.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ADK debug mode
os.environ["ADK_DEBUG"] = "1"
```

### Support

For issues not covered here:
1. Check [Google ADK Documentation](https://ai.google.dev/adk)
2. Review [Alpha Vantage API Docs](https://www.alphavantage.co/documentation/)
3. Search [GitHub Issues](https://github.com/your-repo/issues)

---

## Appendix

### Glossary

- **ADK (Agent Development Kit)**: Google's framework for building multi-agent AI systems
- **A2A Protocol**: Agent-to-Agent communication protocol for interoperability
- **Sharpe Ratio**: Risk-adjusted return metric (higher = better)
- **Beta**: Measure of systematic risk (1.0 = market-like risk)
- **Max Drawdown**: Largest peak-to-trough decline in portfolio value
- **RSI (Relative Strength Index)**: Momentum indicator (0-100 scale)
- **MACD**: Moving Average Convergence Divergence (trend indicator)
- **P/E Ratio**: Price-to-Earnings ratio (valuation metric)

### References

1. [Google ADK Documentation](https://ai.google.dev/adk)
2. [Alpha Vantage API](https://www.alphavantage.co/)
3. [Modern Portfolio Theory](https://en.wikipedia.org/wiki/Modern_portfolio_theory)
4. [Sharpe Ratio Explained](https://www.investopedia.com/terms/s/sharperatio.asp)
5. [A2A Protocol Specification](https://github.com/agent-to-agent/spec)

### License

MIT License - See LICENSE file for details.

### Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

**Last Updated**: February 25, 2026  
**Version**: 2.0.0  
**Author**: Drayvn AI Team  
**Contact**: support@drayvn.ai
