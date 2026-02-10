# Portfolio Swarm Enhancements

This document summarizes the enhancements made to the Portfolio Swarm system.

## New Features

### 1. Optimization Strategies (`portfolio_swarm/strategies.py`)

Users can now select an optimization strategy **after parsing their portfolio**. This allows fine-tuned control over how the swarm agents optimize.

**Available Strategies:**
| Strategy | Risk Level | Description |
|----------|-----------|-------------|
| Aggressive Growth | High | Maximize capital appreciation, higher beta |
| Conservative Income | Low | Prioritize dividends and stability |
| Balanced | Medium | Equal focus on growth and risk |
| Tax Efficient | Medium | Minimize tax impact, loss harvesting |
| ESG Focused | Medium | Sustainability and exclusions |
| Risk Minimization | Low | Defensive positions, low volatility |
| Sector Rotation | Medium | Active sector reallocation |
| Dividend Growth | Medium | Focus on dividend growth companies |
| Custom | Variable | User-defined parameters |

**Usage:**
```python
from portfolio_swarm.strategies import get_strategy, StrategyType, create_custom_strategy

# Use pre-defined strategy
strategy = get_strategy(StrategyType.AGGRESSIVE_GROWTH)

# Create custom strategy
custom = create_custom_strategy(
    name="My Strategy",
    description="Custom optimization",
    base_strategy=StrategyType.BALANCED,
    target_beta=1.2,
    max_drawdown_tolerance=0.25
)

# Pass to orchestrator
orchestrator = SwarmOrchestrator(
    agents=agents,
    strategy=strategy
)
```

### 2. Enhanced Logging (`portfolio_swarm/logger.py`)

Structured logging with session tracking, agent handoff logging, and export capabilities.

**Features:**
- Session-based logging with metrics
- Agent handoff tracking
- JSON/CSV/Text export
- Real-time callbacks for UI updates

**Usage:**
```python
from portfolio_swarm.logger import get_logger

logger = get_logger()
logger.start_session(portfolio_value=50000000, strategy_name="Balanced")
logger.log_agent_handoff("Market Analysis", "Risk Assessment", "Completed analysis")
logger.log_agent_vote("Risk Assessment", "approve", "Within risk tolerance")
logger.end_session(consensus_reached=True, approval_rate=0.8)

# Export
report = logger.export_session_log("json")
```

### 3. Conversation Memory (`portfolio_swarm/memory.py`)

Maintains context across interactions for better multi-turn conversations.

**Features:**
- Windowed message history (configurable size)
- Context persistence
- User preference tracking
- Query templates

**Usage:**
```python
from portfolio_swarm.memory import ConversationMemory, get_query_template

memory = ConversationMemory(window_size=20)
memory.add_user_message("Optimize my portfolio")
memory.set_strategy("Tax Efficient")
memory.set_portfolio_context("$50M portfolio with 12 positions")

# Get context for prompts
context = memory.get_context_string()

# Use query templates
query = get_query_template("tax_harvest")
```

### 4. Enhanced Web UI (`enhanced_web_ui.py`)

New Streamlit interface with strategy selection workflow.

**New Tabs:**
1. **Portfolio** - Load/create portfolio
2. **Strategy** - Select optimization strategy (appears after portfolio parsing)
3. **Optimize** - Run optimization with selected strategy
4. **Results** - View results with agent flow visualization
5. **Docs** - Documentation

**New Features:**
- Strategy selection cards with risk levels
- Custom strategy builder
- Progress visualization during optimization
- Agent flow/interaction graph
- Export results (JSON, CSV, Text)
- Query templates for quick actions

### 6. Flask Web UI Enhancements (Feb 2026)

The Flask UI (`flask_ui.py`) now includes:

**Strategy Selection with Star Ratings:**
- ⭐⭐⭐⭐⭐ rating system for strategies
- **Portfolio-aware ratings** - Ratings dynamically adjust based on:
  - Portfolio beta (high beta → aggressive strategies rated higher)
  - ESG scores (high ESG → esg_focused rated higher)
  - Sector concentration (concentrated → sector_rotation rated lower)
- **BEST FIT** badge on top-rated strategy
- Sorted display (best strategies first)

**Sector Allocation Pie Chart:**
- Chart.js powered visualization
- Shows sector breakdown with percentages
- Colorful sectors with hover tooltips

**Fixed Agent Voting:**
- All 5 agents now vote properly (previously some abstained)
- Added fallback vote parsing when AI doesn't use exact format
- Each agent has context-appropriate defaults

**Fixed Percentage Display:**
- Allocation percentages now display correctly (28.7% not 2869%)
- Fixed double multiplication bug in models.py/index.html

**Multiple Iterations Trigger:**
- Selecting a low-rated strategy causes agents to disagree
- More debate rounds before consensus
- Great for testing swarm pattern behavior

### 5. Updated Orchestrator

The orchestrator now accepts a strategy parameter:

```python
orchestrator = SwarmOrchestrator(
    agents=agents,
    max_iterations=10,
    consensus_threshold=0.6,
    strategy=strategy,  # NEW: Pass optimization strategy
    progress_callback=callback  # Real-time progress updates
)
```

## Running the Enhanced UI

```bash
# Windows
run_enhanced_ui.bat

# Or directly
streamlit run enhanced_web_ui.py
```

## Workflow

1. **Load Portfolio**: Sample, text description, file upload, or custom
2. **Select Strategy**: Choose from templates or create custom
3. **Configure Swarm**: Set iterations, threshold, agents
4. **Run Optimization**: Execute with real-time progress
5. **Review Results**: Agent votes, trade plan, export

## Files Created/Modified

### New Files:
- `portfolio_swarm/strategies.py` - Optimization strategies
- `portfolio_swarm/logger.py` - Enhanced logging
- `portfolio_swarm/memory.py` - Conversation memory
- `enhanced_web_ui.py` - New Streamlit UI
- `run_enhanced_ui.bat` - Windows launcher

### Modified Files:
- `portfolio_swarm/__init__.py` - Added new exports
- `portfolio_swarm/orchestrator.py` - Added strategy support
- `portfolio_swarm/base_agent.py` - Added `set_strategy()` method
