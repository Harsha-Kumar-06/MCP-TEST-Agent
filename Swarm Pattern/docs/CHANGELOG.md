# 📋 Changelog - Portfolio Swarm Optimizer

## [2.1.0] - February 2026

### ⭐ Strategy Enhancements

#### Star Rating System (1-5 Stars)
- All 10 strategies now have **1-5 star ratings** with effectiveness labels
- Ratings reflect risk/reward tradeoff and general applicability:
  - ⭐⭐⭐⭐⭐ **Balanced** - Most reliable for most investors
  - ⭐⭐⭐⭐ Tax Efficient, ESG Focused, Risk Minimization - Specialized excellence
  - ⭐⭐⭐ Conservative Income, Dividend Growth, Value Investing - Solid choices
  - ⭐⭐ Sector Rotation, Momentum Trading - Higher risk/skill required
  - ⭐ Aggressive Growth - Highest risk, not for most investors

#### 2 New Strategies Added
- **Momentum Trading** (2★) - Trend-following based on price momentum
- **Value Investing** (3★) - Fundamental analysis for undervalued stocks

#### Portfolio-Adaptive Ratings
- Ratings now **adjust dynamically** based on YOUR portfolio characteristics
- Adjustments range from -2 to +2 stars based on:
  | Portfolio Trait | Rating Adjustment |
  |-----------------|-------------------|
  | High Beta (>1.2) | Risk Min +1.5★, Aggressive -1.5★ |
  | Low Beta (<0.8) | Aggressive +0.8★, Risk Min -1★ |
  | Low ESG (<65) | ESG Focused +1.5★ |
  | High Sector Concentration (>35%) | Balanced +1★ |
  | Large Portfolio (>$1M) | Tax Efficient +1★ |
- UI shows "📊 For your portfolio:" with personalized reasoning

### 🗳️ Iteration-Aware Voting

#### Agents Now Debate Properly
- **Fixed**: Agents were returning identical votes across iterations
- All 5 agents now have **iteration-aware voting logic**
- Thresholds adjust progressively to encourage consensus:
  | Agent | Base Threshold | Per-Iteration Adjustment |
  |-------|----------------|--------------------------|
  | Market Analysis | 30% bad trades | +5% per iteration |
  | Risk Assessment | 3 violations | +1 per iteration |
  | Tax Strategy | 15% tax liability | +3% per iteration |
  | ESG Compliance | ESG 60 avg | -3 per iteration |
  | Algorithmic Trading | 50 bps cost | +10 bps per iteration |
- Agents become more lenient after iteration 2-3
- Vote rationale includes iteration context (e.g., "Iter 3: threshold 45%")

### 🐛 Bug Fixes
- **Irrelevant content filter**: Changed from single keywords to specific phrases
  - Old: Blocked on `'modern'` → false positives
  - New: Blocks on `'welcome to the world'`, `'exciting journey'` etc.
- **BUY trade generation**: Added proper BUY trade logic (was only SELLs)

### 📁 Files Modified
- `portfolio_swarm/strategies.py` - 10 strategies with star_rating, effectiveness, best_for
- `portfolio_swarm/agents.py` - Iteration-aware vote_on_proposal for all 5 agents
- `templates/index.html` - Portfolio-adaptive getStrategyRating(), displayStrategyCards()

---

## [2.0.0] - February 2026

### 🚀 Major Changes

#### API Migration
- **Migrated from `google-generativeai` to `google.genai`** (new official SDK)
  - The deprecated `google-generativeai` package was returning irrelevant responses
  - New `google.genai` package provides reliable, properly-formatted responses
  - Uses `genai.Client()` for API initialization

#### Model Updates
- **Default model**: `gemini-2.5-flash` (upgraded from `gemini-1.5-flash`)
- **Max tokens**: 4096 (increased from 2048)
- **Temperature**: 0.5 (adjusted from 0.3)

### ⚡ Performance Optimizations

#### Rule-Based Voting (50% reduction in API calls)
- All 5 agents now use **rule-based logic** for voting instead of AI
- Voting decisions based on quantifiable metrics:
  - **Market Analysis**: Checks trade count and sector alignment
  - **Risk Assessment**: Evaluates compliance violations
  - **Tax Strategy**: Calculates actual tax liability percentage
  - **ESG Compliance**: Checks portfolio average ESG score
  - **Algorithmic Trading**: Estimates execution costs in basis points
- **Benefit**: 10 calls per iteration → 5 calls (only analysis uses AI)

#### Analysis Caching (eliminates redundant calls)
- AI analysis is cached after first iteration
- Subsequent iterations reuse cached results if portfolio unchanged
- Cache key based on portfolio positions hash

### 🐛 Bug Fixes
- Fixed `'Portfolio' object has no attribute 'holdings'` → changed to `positions`
- Fixed type checker errors for optional None values
- Added proper null checks for `gemini_client` and `types`
- Fixed `response.text` potentially being None

### 📁 Files Modified
- `portfolio_swarm/agents.py` - All 5 agent classes updated
- `portfolio_swarm/base_agent.py` - Added caching methods
- `portfolio_swarm/text_parser.py` - Updated to new API
- `portfolio_swarm/config.py` - Updated model defaults
- `.env` - New configuration options

### 🔧 Configuration Changes

```env
# Updated .env settings
GEMINI_MODEL=gemini-2.5-flash      # Was: gemini-1.5-flash
GEMINI_MAX_TOKENS=4096             # Was: 2048
GEMINI_TEMPERATURE=0.5             # Was: 0.3
ENABLE_DEBUG_LOGGING=false         # New option
```

### 📦 Dependencies

```bash
# Install the NEW package (required)
pip install google-genai

# Do NOT use the deprecated package
# pip install google-generativeai  # ❌ Deprecated
```

---

## [1.5.0] - February 2026

### Features
- Strategy selection with 8 optimization strategies
- Portfolio-aware ratings based on YOUR holdings
- Sector pie chart visualization
- Star ratings for strategies and trades
- Enhanced voting (all 5 agents participate)
- Multiple iterations with configurable min/max

### UI Improvements
- Flask-based web interface
- Real-time terminal logging
- File upload (CSV, JSON, YAML)
- Text portfolio parsing

---

## [1.0.0] - Initial Release

### Core Features
- 5 specialized AI agents
- Communication bus for inter-agent messaging
- Consensus mechanism with voting
- Swarm orchestrator for iteration management
- Demo with $50M portfolio scenario
