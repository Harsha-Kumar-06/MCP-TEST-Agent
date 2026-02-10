# Quick Start Guide - Financial Portfolio Swarm

## ✅ What We Built

A complete **swarm pattern** implementation for portfolio optimization with:

- 🤖 **5 Specialized Agents** (Market, Risk, Tax, ESG, Trading)
- 💬 **Communication Bus** for inter-agent messaging
- 🎯 **Consensus Mechanism** with voting and approval thresholds
- 📊 **Demo Scenario** - $50M portfolio rebalancing

---

## 🚀 Run the Demo (3 Steps)

### 1. Navigate to project
```bash
cd "c:\Users\Harsha Kumar\Desktop\DRAVYN\Agents\Swarm Pattern"
```

### 2. Run the demo (choose one)
```bash
# Option A: Quick launch script (Windows)
run_demo.bat

# Option B: Python command
python demo.py

# Option C: Web UI (Recommended)
run_web.bat
# or: python flask_ui.py
```

### 3. Watch the agents collaborate!

---

## 📁 Project Structure

```
Swarm Pattern/
├── portfolio_swarm/          # Core package
│   ├── models.py            # Data models (Portfolio, Trade, Vote)
│   ├── communication.py     # Message bus
│   ├── base_agent.py        # Abstract agent class
│   ├── agents.py            # 5 specialized agents
│   ├── orchestrator.py      # Swarm coordinator
│   ├── input_parser.py      # File parsing
│   ├── text_parser.py       # Text parsing
│   └── text_parser_gemini.py # AI-powered parsing
├── flask_ui.py              # Main Web UI
├── cli_interface.py         # Command-line interface
├── demo.py                  # Basic demo
├── run_web.bat              # Quick launch Web UI
├── run_cli.bat              # Quick launch CLI
├── run_demo.bat             # Quick launch demo
├── templates/               # HTML templates
├── docs/                    # Documentation
├── samples/                 # Sample portfolios
├── tests/                   # Test files
└── README.md                # Main documentation
```

---

## 🎯 What the Demo Shows

**Problem:**
- Portfolio has 32.2% in Technology (exceeds 30% limit)
- Mix of short-term/long-term positions (tax implications)
- Some holdings below ESG minimums

**Solution Process:**
1. **Market Agent**: "Tech is overvalued, reduce exposure"
2. **Risk Agent**: "CRITICAL - compliance violation, fix NOW"
3. **Tax Agent**: "If we sell NVDA, triggers $250K in taxes"
4. **ESG Agent**: "Don't buy low-ESG replacements"
5. **Trading Agent**: "Executable in 1-2 days, $537 cost"

**Result:**
- ✅ **80% approval rate** (4 of 5 agents approve)
- ✅ Consensus reached in **1 iteration**
- ✅ Compliance fixed (32.2% → 30%)
- ✅ Tax liability minimized ($40K vs $250K)

---

## 🔧 How to Customize

### Change Consensus Rules

Edit in `demo.py`:
```python
orchestrator = SwarmOrchestrator(
    agents=agents,
    max_iterations=10,        # Increase for more debate rounds
    consensus_threshold=0.8,  # Require 80% approval
    require_unanimous=False   # Set True for 100% agreement
)
```

### Modify Portfolio

Edit `create_sample_portfolio()` in `demo.py`:
```python
Position(
    ticker="TSLA",           # Your stock
    shares=5000,
    current_price=250.0,
    cost_basis=200.0,
    acquisition_date=datetime.now() - timedelta(days=400),
    sector="Technology",
    esg_score=65,
    beta=2.0
)
```

### Add New Agent

See `llm_integration_example.py` for template

---

## 🧪 Test Different Scenarios

### Scenario 1: Unanimous Required
```python
orchestrator = SwarmOrchestrator(
    agents=agents,
    require_unanimous=True  # All agents must approve
)
```
**Expected**: More iterations, harder to reach consensus

### Scenario 2: Tax-Heavy Conflict
Add more short-term positions to trigger tax agent rejection:
```python
Position(
    ticker="NVDA",
    acquisition_date=datetime.now() - timedelta(days=300),  # 10 months
    # ... large unrealized gain
)
```

### Scenario 3: ESG Violations
Add low-ESG positions to create ESG agent concerns:
```python
Position(
    ticker="XOM",  # Energy sector
    esg_score=45,  # Below 60 minimum
    # ...
)
```

---

## 📊 Understanding the Output

### Iteration Flow
```
ITERATION 1
  Phase 1: Parallel Analysis
    - Each agent analyzes independently
    - Broadcasts findings (conviction 1-10)
  
  Phase 2: Inter-Agent Debate
    - Agents challenge each other's recommendations
    - Exchange messages
  
  Phase 3: Proposal Collection
    - Agents propose trade plans
    - Best proposal selected
  
  Phase 4: Voting
    - All agents vote: APPROVE/REJECT/ABSTAIN
    - Calculate approval rate
```

### Vote Symbols
- ✅ **APPROVE** - Agent supports the plan
- ❌ **REJECT** - Agent opposes the plan
- ⚠️ **ABSTAIN** - Agent is neutral

### Key Metrics
```
Approval Rate: 80.0% (4 of 5 agents)
Iterations Used: 1/10
Total Messages: 5
Consensus: ACHIEVED ✅
```

---

## 🎓 Key Concepts Demonstrated

### 1. All-to-All Communication
Any agent can message any other agent:
```python
tax_agent.send_message(
    "Selling now triggers $250K tax, wait 2 weeks",
    to_agent=AgentType.MARKET_ANALYSIS
)
```

### 2. Iterative Refinement
- Iteration 1: Initial proposals → Tax agent rejects
- Iteration 2: Revised proposals → Alternative found
- Iteration 3: Consensus reached ✅

### 3. Exit Conditions
- **Max iterations**: 10 (prevents infinite loops)
- **Consensus threshold**: 60% (3 of 5 agents)
- **Time limit**: Could add timeout
- **Goal achieved**: Compliance fixed + consensus

### 4. No Central Supervisor
- No single agent "in charge"
- Dispatcher only facilitates, doesn't orchestrate
- Agents self-organize through debate

---

## 💡 Production Enhancements

To make this production-ready:

### 1. Add LLM Integration
```python
# Instead of rule-based logic:
if position.sector == "Technology":
    return "Overvalued"

# Use LLM reasoning:
analysis = llm.complete(
    f"Analyze {position.ticker} in {position.sector} sector. "
    f"P/E: {pe_ratio}, Beta: {beta}. Market outlook: {context}"
)
```

### 2. Real Market Data
```python
# Replace mock data:
self.sector_valuations = {...}

# With live feeds:
self.market_data = BloombergAPI.get_sector_metrics()
```

### 3. Advanced Risk Models
```python
# Add real VaR calculation:
var = calculate_var(
    portfolio_returns,
    confidence=0.95,
    time_horizon=1
)
```

### 4. Backtesting Framework
```python
# Test on historical data:
results = backtest_swarm(
    start_date="2020-01-01",
    end_date="2024-01-01",
    rebalancing_frequency="quarterly"
)
```

---

## 🐛 Troubleshooting

**Issue**: "No consensus reached after 10 iterations"
- **Solution**: Lower `consensus_threshold` or increase `max_iterations`

**Issue**: "Tax agent always rejects"
- **Solution**: Adjust tax logic or add more long-term positions

**Issue**: "ESG agent blocks everything"
- **Solution**: Lower `esg_minimum` or use higher-ESG securities

---

## 📚 Next Steps

1. ✅ **Run demo.py** - See it work
2. 🌐 **Try flask_ui.py** - Full web interface at http://localhost:5000
3. 📖 **Read docs/financial_portfolio_optimization.md** - Understand use case
4. 🔧 **Modify demo.py** - Try different portfolios
5. 🤖 **Add LLM** - See llm_integration_example.py
6. 📁 **Sample inputs** - Check samples/ folder for portfolio templates

---

## 🎯 Learning Objectives Achieved

✅ Understand swarm pattern architecture
✅ Implement multi-agent communication
✅ Build consensus mechanisms
✅ Handle competing objectives
✅ Create production-ready structure

---

## 💬 Questions?

**Q: Why didn't agents debate more?**
A: Risk agent's compliance violation had conviction 10/10, creating strong consensus

**Q: How to force more iterations?**
A: Increase `consensus_threshold` to 0.9 or add conflicting constraints

**Q: Can I add more agents?**
A: Yes! Create new class inheriting from `BaseAgent`, add to swarm

**Q: How to integrate with real brokers?**
A: Extend `AlgorithmicTradingAgent` to call broker APIs (Alpaca, Interactive Brokers)

---

## 🏆 Success!

You now have a fully functional multi-agent swarm system! 🎉

The code is modular, extensible, and ready for real-world enhancements.
