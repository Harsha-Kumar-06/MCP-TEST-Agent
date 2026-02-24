# System Architecture - Financial Portfolio Swarm

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Web UI       │  │ CLI          │  │ REST API     │             │
│  │ (Streamlit)  │  │ (Interactive)│  │ (Production) │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
└─────────┼──────────────────┼──────────────────┼─────────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                      SWARM ORCHESTRATOR                              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  • Manages iteration cycles (1-10)                             │ │
│  │  • Tracks consensus (threshold: 60%)                           │ │
│  │  • Coordinates agent communication                             │ │
│  │  • Handles exit conditions                                     │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                    COMMUNICATION BUS                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  • Message routing (agent-to-agent, broadcast)                 │ │
│  │  • History tracking (full audit trail)                         │ │
│  │  • Subscribe/publish pattern                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
┌─────────▼─────────┐              ┌───────────▼──────────┐
│  SPECIALIZED      │              │  SPECIALIZED         │
│  AGENTS           │              │  AGENTS              │
│                   │              │                      │
│ ┌───────────────┐ │              │ ┌────────────────┐  │
│ │ Market        │ │              │ │ Tax Strategy   │  │
│ │ Analysis      │ │              │ │ Agent          │  │
│ │ Agent         │ │              │ │                │  │
│ │               │ │              │ │ • Tax lots     │  │
│ │ • Valuations  │ │              │ │ • Gains/losses │  │
│ │ • Trends      │ │              │ │ • Timing       │  │
│ │ • Sentiment   │ │              │ └────────────────┘  │
│ └───────────────┘ │              │                      │
│                   │              │ ┌────────────────┐  │
│ ┌───────────────┐ │              │ │ ESG Compliance │  │
│ │ Risk          │ │              │ │ Agent          │  │
│ │ Assessment    │ │              │ │                │  │
│ │ Agent         │ │              │ │ • ESG scores   │  │
│ │               │ │              │ │ • Sustainability│ │
│ │ • Compliance  │ │              │ │ • Controversies│  │
│ │ • VaR/Beta    │ │              │ └────────────────┘  │
│ │ • Limits      │ │              │                      │
│ └───────────────┘ │              │ ┌────────────────┐  │
│                   │              │ │ Algorithmic    │  │
└───────────────────┘              │ │ Trading Agent  │  │
                                   │ │                │  │
                                   │ │ • Execution    │  │
                                   │ │ • Liquidity    │  │
                                   │ │ • VWAP/TWAP    │  │
                                   │ └────────────────┘  │
                                   └─────────────────────┘
                                             │
┌────────────────────────────────────────────▼─────────────────────────┐
│                      EXTERNAL INTEGRATIONS                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Market Data│  │ Brokerages │  │ ESG Data   │  │ Monitoring   │  │
│  │            │  │            │  │            │  │              │  │
│  │ • Polygon  │  │ • Alpaca   │  │ • MSCI     │  │ • DataDog    │  │
│  │ • Bloomberg│  │ • IB       │  │ • Sustain. │  │ • Sentry     │  │
│  │ • Alpha V. │  │ • TD       │  │            │  │ • Slack      │  │
│  └────────────┘  └────────────┘  └────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
┌──────────────┐
│ 1. USER INPUT│
│              │
│ • Portfolio  │
│ • Constraints│
│ • Preferences│
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│ 2. PORTFOLIO ANALYSIS            │
│                                  │
│ ┌────────────────────────────┐  │
│ │ All Agents Analyze in      │  │
│ │ Parallel                   │  │
│ │                            │  │
│ │ • Market conditions        │  │
│ │ • Compliance checks        │  │
│ │ • Tax implications         │  │
│ │ • ESG scoring              │  │
│ │ • Execution feasibility    │  │
│ └────────────────────────────┘  │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 3. ITERATIVE DEBATE              │
│    (Rounds 1-10)                 │
│                                  │
│ ┌────────────────────────────┐  │
│ │ Agents Exchange Messages   │  │
│ │                            │  │
│ │ Market: "Tech overvalued"  │  │
│ │ Tax:    "Triggers $250K"   │  │
│ │ Risk:   "Fix compliance!"  │  │
│ │ ESG:    "Check scores"     │  │
│ │ Trading:"Feasible in 2d"   │  │
│ └────────────────────────────┘  │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 4. PROPOSAL GENERATION           │
│                                  │
│ ┌────────────────────────────┐  │
│ │ Agents Propose Trade Plans │  │
│ │                            │  │
│ │ • Sell NVDA $5M            │  │
│ │ • Buy JNJ $2.5M            │  │
│ │ • Buy PFE $2.5M            │  │
│ └────────────────────────────┘  │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 5. VOTING & CONSENSUS            │
│                                  │
│ ┌────────────────────────────┐  │
│ │ Each Agent Votes           │  │
│ │                            │  │
│ │ ✅ Market:  APPROVE (8/10) │  │
│ │ ✅ Risk:    APPROVE (10/10)│  │
│ │ ✅ Tax:     APPROVE (7/10) │  │
│ │ ❌ ESG:     REJECT (10/10) │  │
│ │ ✅ Trading: APPROVE (8/10) │  │
│ │                            │  │
│ │ Result: 80% approval ✅    │  │
│ └────────────────────────────┘  │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 6. EXECUTION (if consensus)      │
│                                  │
│ ┌────────────────────────────┐  │
│ │ • Validate with broker     │  │
│ │ • Calculate exact tax      │  │
│ │ • Submit orders            │  │
│ │ • Monitor execution        │  │
│ │ • Log results              │  │
│ └────────────────────────────┘  │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────┐
│ 7. OUTPUT    │
│              │
│ • Trade plan │
│ • Tax impact │
│ • Rationales │
│ • Audit log  │
└──────────────┘
```

---

## 📦 Component Details

### 1. Agent Base Class
```python
BaseAgent (Abstract)
├── analyze(portfolio) → AgentAnalysis     # Uses AI (Gemini)
├── propose_solution() → AgentProposal     # Rule-based
├── vote_on_proposal() → AgentVote         # Rule-based (optimized)
├── send_message() → void
├── _should_use_cached_analysis() → bool   # Caching support
└── _cache_analysis() → void               # Caching support
```

### 2. API Integration
```python
# New google.genai API (v1.64.0+)
from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        temperature=0.5,
        max_output_tokens=4096,
    )
)
```

### 2. Specialized Agents

**Market Analysis Agent**
- Input: Portfolio positions, market data
- Output: Valuation assessments, recommendations
- Data: P/E ratios, momentum, sentiment

**Risk Assessment Agent**
- Input: Portfolio allocations, limits
- Output: Compliance status, risk metrics
- Data: Beta, VaR, sector exposure

**Tax Strategy Agent**
- Input: Tax lots, acquisition dates
- Output: Tax liability estimates, alternatives
- Data: Short/long-term gains, wash sales

**ESG Compliance Agent**
- Input: Holdings, ESG criteria
- Output: ESG scores, compliance status
- Data: E/S/G ratings, controversies

**Algorithmic Trading Agent**
- Input: Trade sizes, market conditions
- Output: Execution costs, timeline
- Data: Liquidity, spreads, volume

### 3. Communication Flow

```
Message Types:
├── analysis: Initial findings broadcast
├── debate: Agent-to-agent challenges
├── proposal: Trade plan submission
└── vote: Approval/rejection with rationale

Message Structure:
{
  "from_agent": "market_analysis",
  "to_agent": "tax_strategy" (or null for broadcast),
  "content": "Selling now triggers $250K tax",
  "iteration": 2,
  "timestamp": "2026-02-03T15:45:23Z"
}
```

---

## 🎯 Consensus Algorithm

```
For each iteration (max 15):
  1. All agents analyze portfolio (AI - cached after first iteration)
  2. Agents debate via messages (AI)
  3. Collect proposals from agents (rule-based)
  4. Select best proposal (highest conviction)
  5. All agents vote on proposal (rule-based - no AI)
  6. Calculate approval rate
  
  If iteration < min_iterations:
    CONTINUE regardless of approval rate
  
  If approval_rate >= threshold (configurable 50-85%):
    CONSENSUS ACHIEVED ✅
    Execute trade plan
    EXIT
  
  If iteration == max:
    NO CONSENSUS ❌
    Execute fallback (compliance-first)
    EXIT
```

---

## ⚡ Performance Optimizations

### 1. Rule-Based Voting (50% API reduction)

Voting now uses deterministic logic instead of AI calls:

| Agent | Voting Logic |
|-------|-------------|
| **Market Analysis** | Checks trade count, sector alignment |
| **Risk Assessment** | Evaluates compliance violations |
| **Tax Strategy** | Calculates tax liability % of portfolio |
| **ESG Compliance** | Checks portfolio avg ESG ≥ 60 |
| **Algorithmic Trading** | Estimates execution cost in bps |

### 1b. Iteration-Aware Voting (Feb 2026)

Voting thresholds now adjust progressively to encourage consensus:

| Agent | Base Threshold | Per-Iteration Adjustment |
|-------|----------------|--------------------------|
| **Market Analysis** | 30% bad trades | +5% tolerance per iteration |
| **Risk Assessment** | 3 violations | +1 allowed per iteration |
| **Tax Strategy** | 15% tax liability | +3% tolerance per iteration |
| **ESG Compliance** | ESG avg ≥ 60 | -3 threshold per iteration |
| **Algorithmic Trading** | 50 bps cost | +10 bps tolerance per iteration |

**Behavior:**
- Iteration 1: Strict thresholds for high-quality proposals
- Iteration 2-3: Moderate leniency, some compromise
- Iteration 4+: High leniency, focus on reaching consensus
- Vote rationale includes iteration context (e.g., "Iter 3: threshold 45%")

```python
# Example: Tax Strategy voting logic
total_value = portfolio.total_value
gain_pct = (total_tax / total_value) * 100
if total_tax > 100000 and gain_pct > 2.0:
    vote_type = VoteType.REJECT
else:
    vote_type = VoteType.APPROVE
```

### 2. Analysis Caching (eliminates redundant AI calls)

```python
def _should_use_cached_analysis(self, portfolio):
    if self.current_iteration == 0:
        return False
    return self._get_portfolio_hash(portfolio) == self._last_portfolio_hash

# Result: 5 AI calls on iteration 1, 0 AI calls on iterations 2+
```

### 3. API Call Summary

| Operation | Before | After |
|-----------|--------|-------|
| Analysis (per agent) | 1 AI call | 1 AI call (cached) |
| Debate (per agent) | 1 AI call | 1 AI call |
| Voting (per agent) | 1 AI call | 0 (rule-based) |
| **Total per iteration** | 15 calls | 5-10 calls |

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────┐
│         SECURITY LAYERS                 │
│                                         │
│  1. API Authentication                  │
│     • API keys in .env                  │
│     • JWT tokens for web UI             │
│     • OAuth for brokerages              │
│                                         │
│  2. Data Encryption                     │
│     • TLS for all API calls             │
│     • Encrypted storage for positions   │
│     • Secrets manager (AWS/GCP)         │
│                                         │
│  3. Access Control                      │
│     • Role-based permissions            │
│     • Audit logging (who/what/when)     │
│     • IP whitelisting                   │
│                                         │
│  4. Validation                          │
│     • Input sanitization                │
│     • Output validation                 │
│     • Trade limit checks                │
└─────────────────────────────────────────┘
```

---

## 🎯 Strategy Selection System

### 10 Available Strategies

| Strategy | Stars | Effectiveness | Best For |
|----------|-------|---------------|----------|
| **Balanced** | ⭐⭐⭐⭐⭐ | Excellent | Most investors |
| **Tax Efficient** | ⭐⭐⭐⭐ | Excellent | High-tax situations |
| **ESG Focused** | ⭐⭐⭐⭐ | Very Good | Sustainable investors |
| **Risk Minimization** | ⭐⭐⭐⭐ | Very Good | Conservative investors |
| **Conservative Income** | ⭐⭐⭐ | Good | Retirees, income seekers |
| **Dividend Growth** | ⭐⭐⭐ | Good | Long-term holders |
| **Value Investing** | ⭐⭐⭐ | Good | Patient investors |
| **Sector Rotation** | ⭐⭐ | Moderate | Active traders |
| **Momentum Trading** | ⭐⭐ | Moderate | Trend followers |
| **Aggressive Growth** | ⭐ | Variable | High risk tolerance |

### Portfolio-Adaptive Ratings

Ratings adjust ±2 stars based on portfolio characteristics:

```
getStrategyRating(strategy, portfolio):
  baseRating = strategy.star_rating
  adjustment = 0
  reason = []
  
  # High-beta portfolios need risk management
  if portfolio.beta > 1.2:
    if strategy == "Risk Minimization": adjustment += 1.5
    if strategy == "Aggressive Growth": adjustment -= 1.5
  
  # Low-ESG portfolios benefit from ESG strategy
  if portfolio.avg_esg < 65:
    if strategy == "ESG Focused": adjustment += 1.5
  
  # High sector concentration needs diversification
  if portfolio.max_sector_pct > 35%:
    if strategy == "Balanced": adjustment += 1.0
  
  # Large portfolios benefit from tax optimization
  if portfolio.total_value > $1M:
    if strategy == "Tax Efficient": adjustment += 1.0
  
  return clamp(baseRating + adjustment, 1, 5)
```

---

## 📊 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION DEPLOYMENT                     │
│                                                              │
│  ┌────────────────┐      ┌──────────────┐                  │
│  │ Load Balancer  │──────│ Web Server   │                  │
│  │ (nginx)        │      │ (Gunicorn)   │                  │
│  └────────────────┘      └──────┬───────┘                  │
│                                  │                           │
│  ┌────────────────────────────────┴─────────────────┐      │
│  │          Application Cluster                     │      │
│  │  ┌──────────────┐  ┌──────────────┐             │      │
│  │  │ Swarm        │  │ Swarm        │             │      │
│  │  │ Instance 1   │  │ Instance 2   │ ...         │      │
│  │  └──────────────┘  └──────────────┘             │      │
│  └──────────────────────────────────────────────────┘      │
│                                  │                           │
│  ┌────────────────┐      ┌──────▼───────┐                  │
│  │ Redis Cache    │      │ PostgreSQL   │                  │
│  │ (sessions)     │      │ (portfolios) │                  │
│  └────────────────┘      └──────────────┘                  │
│                                                              │
│  ┌────────────────┐      ┌──────────────┐                  │
│  │ Task Queue     │      │ Monitoring   │                  │
│  │ (Celery)       │      │ (DataDog)    │                  │
│  └────────────────┘      └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 State Machine

```
Portfolio State Machine:

   ┌───────────┐
   │  CREATED  │
   └─────┬─────┘
         │
         ▼
   ┌───────────┐     Analysis
   │ ANALYZING │◄──────────┐
   └─────┬─────┘           │
         │                 │
         ▼                 │
   ┌───────────┐    No     │
   │  DEBATING │◄─────┐    │
   └─────┬─────┘      │    │
         │ Consensus? │    │
         ▼            │    │
   ┌───────────┐ No  │    │
   │  VOTING   │─────┘    │
   └─────┬─────┘          │
         │ Yes            │
         ▼                │
   ┌───────────┐          │
   │ EXECUTING │          │
   └─────┬─────┘          │
         │                │
         ▼                │
   ┌───────────┐  Retry   │
   │ COMPLETED │──────────┘
   └───────────┘
```

---

## 📈 Scalability Considerations

**Current (Demo):**
- Single-threaded
- In-memory state
- Local execution
- 1 portfolio at a time

**Production (Scalable):**
- Multi-threaded agent analysis
- Database-backed state
- Distributed processing (Celery)
- Handle 1000s of portfolios concurrently

**Performance Targets:**
- Analysis: <5 seconds
- Consensus: <30 seconds
- Total rebalancing: <2 minutes

---

## 🧪 Testing Strategy

```
Testing Pyramid:

      ┌──────────────┐
      │  E2E Tests   │  (Full swarm scenarios)
      └──────────────┘
     ┌────────────────┐
     │ Integration    │  (Agent communication)
     └────────────────┘
    ┌──────────────────┐
    │  Unit Tests      │  (Individual agent logic)
    └──────────────────┘
   ┌────────────────────┐
   │  Property Tests    │  (Consensus properties)
   └────────────────────┘
```

---

## 🎓 Key Design Patterns

1. **Abstract Factory** - Agent creation
2. **Observer** - Communication bus (pub/sub)
3. **Strategy** - Different agent implementations
4. **State** - Swarm iteration states
5. **Command** - Trade execution
6. **Composite** - Portfolio structure

---

## 📚 Technology Stack

**Backend:**
- Python 3.11+
- Type hints (mypy)
- Logging (structlog)

**Frontend:**
- Streamlit (Web UI)
- Click (CLI)

**External:**
- OpenAI/Anthropic (LLM)
- Polygon/Bloomberg (Market data)
- Alpaca (Brokerage)
- DataDog (Monitoring)

**Infrastructure:**
- Docker containers
- Kubernetes (orchestration)
- PostgreSQL (storage)
- Redis (caching)

---

This architecture supports:
✅ Horizontal scaling
✅ High availability
✅ Real-time processing
✅ Comprehensive monitoring
✅ Production-grade security
