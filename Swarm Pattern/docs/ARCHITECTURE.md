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
├── analyze(portfolio) → AgentAnalysis
├── propose_solution() → AgentProposal
├── vote_on_proposal() → AgentVote
└── send_message() → void
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
For each iteration (max 10):
  1. All agents analyze portfolio
  2. Agents debate via messages
  3. Collect proposals from agents
  4. Select best proposal (highest conviction)
  5. All agents vote on proposal
  6. Calculate approval rate
  
  If approval_rate >= threshold (60%):
    CONSENSUS ACHIEVED ✅
    Execute trade plan
    EXIT
  
  If iteration == max:
    NO CONSENSUS ❌
    Execute fallback (compliance-first)
    EXIT
```

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
