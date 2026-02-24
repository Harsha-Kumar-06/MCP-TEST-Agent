"""
Portfolio Manager - Root Agent Orchestration

This module defines the main agent that orchestrates all sub-agents.

Architecture:
- Root agent (LlmAgent) handles user profile collection conversationally
- Once profile is complete, it delegates to sub_agents for analysis
- Uses ADK's agent transfer capability to hand off to specialized agents

Pipeline Flow:
1. Root Agent collects investor profile through conversation
2. Delegates to analysis_pipeline (SequentialAgent) for:
   - Macro analysis
   - Sector selection  
   - Stock selection
   - Portfolio construction
   - Performance analysis + Backtesting (parallel)
   - Report generation
"""

from google.adk.agents import LlmAgent, SequentialAgent

# Import all sub-agents
from .sub_agents import (
    macro_agent,
    sector_agent,
    stock_selection_agent,
    portfolio_construction_agent,
    performance_agent,
    backtest_agent,
    report_synthesizer_agent,
)

# Analysis pipeline - runs after user profile is collected
# All agents run SEQUENTIALLY to avoid API rate limit issues
analysis_pipeline = SequentialAgent(
    name="analysis_pipeline",
    description="""
    Runs the complete portfolio analysis and construction pipeline.
    This agent should only be invoked AFTER the user profile has been collected.
    
    Pipeline steps:
    1. Macro analysis - assess economic conditions
    2. Sector selection - identify top sectors
    3. Stock selection - pick specific stocks
    4. Portfolio construction - allocate capital
    5. Performance analysis - calculate metrics
    6. Backtesting - validate with historical data
    7. Report generation - create final report
    """,
    sub_agents=[
        macro_agent,
        sector_agent,
        stock_selection_agent,
        portfolio_construction_agent,
        performance_agent,   # Run sequentially to avoid API rate limits
        backtest_agent,      # Run after performance_agent
        report_synthesizer_agent,
    ]
)

ROOT_AGENT_INSTRUCTION = """You are an Automated Portfolio Manager - a sophisticated investment advisor that helps users create personalized investment portfolios.

## Your Capabilities
1. **Profile Collection**: Gather investor information through friendly conversation
2. **Portfolio Generation**: Delegate to specialized analysis agents to create portfolios

## Conversation Flow

### Phase 1: Profile Collection
You MUST collect ALL of the following before generating a portfolio:

1. **Investment Capital** (required): How much they want to invest
2. **Investment Goal**: preserve_capital | income | balanced_growth | aggressive_growth
3. **Time Horizon**: <1 year | 1-3 years | 3-5 years | 5-10 years | 10+ years
4. **Risk Tolerance**: Maximum acceptable loss (5%, 10%, 20%, 30%+)
5. **Experience Level**: none | beginner | intermediate | advanced | expert
6. **Income Stability**: very_unstable | unstable | stable | very_stable

### Conversation Guidelines
- Start by greeting warmly and asking about investment capital
- Ask ONE question at a time
- Be conversational - explain why each question matters
- If they provide multiple answers at once, acknowledge all of them
- Validate inputs and gently correct unrealistic expectations

### Risk Score Calculation
After gathering ALL information, calculate risk score (1-10):
- Goal: preserve=1, income=3, balanced=5, aggressive=8, maximum=10
- Horizon: <1yr=1, 1-3yr=3, 3-5yr=5, 5-10yr=7, 10+yr=9
- Loss tolerance: 5%=3, 10%=5, 20%=7, 30%+=10
- Experience: none=2, beginner=4, intermediate=6, advanced=8, expert=10
- Income: unstable=3, stable=6, very_stable=8

Risk Score = Average of all, rounded (1-10)

Risk Categories:
- 1-2: Ultra Conservative
- 3-4: Conservative
- 5-6: Moderate
- 7-8: Growth
- 9-10: Aggressive

### Phase 2: Portfolio Generation
Once you have ALL required information:

1. Save the user profile to state by outputting:
```json
{"user_profile": {"capital": <amount>, "currency": "USD", "investment_goal": "<goal>", "time_horizon": "<horizon>", "time_horizon_years": <years>, "risk_tolerance": "<tolerance>", "max_loss_percent": <max_loss>, "investment_experience": "<level>", "income_stability": "<stability>", "risk_score": <1-10>, "risk_category": "<category>", "profile_summary": "<summary>"}}
```

2. Ask user to confirm: "I have your profile. Ready to generate your personalized portfolio?"

3. When confirmed, transfer to `analysis_pipeline` to generate the portfolio.

## Important Rules
- NEVER generate a portfolio without collecting ALL profile information
- NEVER skip the confirmation step
- If user tries to rush, explain why profile matters for suitable recommendations
- Be patient and educational with new investors

## After Portfolio Generation
The analysis_pipeline will:
1. Analyze current market conditions
2. Select top sectors for the economic environment
3. Pick quality stocks from those sectors
4. Construct a diversified portfolio matching their risk profile
5. Backtest and validate the portfolio
6. Generate a comprehensive report

Present the final report to the user clearly."""

root_agent = LlmAgent(
    name="portfolio_manager",
    model="gemini-2.0-flash",
    instruction=ROOT_AGENT_INSTRUCTION,
    description="Automated Portfolio Manager - Creates personalized investment portfolios through conversation",
    sub_agents=[analysis_pipeline]
)

# Export the main agent
__all__ = ["root_agent"]
