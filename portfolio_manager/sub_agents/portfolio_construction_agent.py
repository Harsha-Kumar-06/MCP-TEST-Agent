"""
Portfolio Construction Agent

This agent allocates capital to the selected stocks based on
the user's risk profile and diversification requirements.
"""

import json
import os
from google.adk.agents import LlmAgent

# Import calculation tools
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.calculations import (
    calculate_correlation_matrix,
    calculate_portfolio_volatility,
    calculate_portfolio_return
)
from tools.stock_api import get_historical_prices

# Load risk profiles
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def get_risk_profile_config() -> dict:
    """
    Get risk profile configuration for portfolio allocation.
    
    Returns:
        dict: Risk profile constraints including:
            - allocation rules per risk level
            - max position sizes
            - diversification requirements
    
    Example:
        >>> get_risk_profile_config()
        {
            'risk_profiles': {
                '5': {'name': 'Balanced', 'max_single_stock': 12, ...}
            }
        }
    """
    try:
        with open(os.path.join(DATA_DIR, "risk_profiles.json"), "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


PORTFOLIO_CONSTRUCTION_INSTRUCTION = """You are a portfolio construction specialist responsible for allocating capital across selected stocks.

## Available Context
Review the conversation history for:
- user_profile: Investor's risk profile (capital, risk_score)
- selected_stocks: Stocks chosen by the Stock Selection Agent
- macro_outlook: Market conditions from Macro Agent

## Your Task
1. Call `get_risk_profile_config` to get allocation rules for the user's risk score
2. Optionally use `get_historical_prices` for a few key stocks to check correlations
3. Use `calculate_correlation_matrix` if you have return data
4. Allocate capital according to constraints
5. Ensure proper diversification

## CRITICAL CAPITAL CONSTRAINT
**The total value of all positions combined MUST NOT exceed total_capital.**
Every dollar calculation below must be derived from the user's total_capital.

## Allocation Methodology

### Step 1: Determine Cash Reserve
Based on risk score, decide cash_reserve_percent:
- Risk score 1-3: cash_reserve_percent = 15 (keep 15% cash)
- Risk score 4-6: cash_reserve_percent = 7 (keep 7% cash)
- Risk score 7-10: cash_reserve_percent = 3 (keep 3% cash)

```
cash_reserve_amount = total_capital * cash_reserve_percent / 100
invested_capital = total_capital - cash_reserve_amount
```

### Step 2: Determine Stock Weights
Assign a weight_percent to each stock such that ALL weights sum to exactly 100%:
- Equal Weight: start with (100 / number_of_stocks) for each
- Adjust based on scores and risk constraints
- Apply max per-stock constraint (see Step 3)
- **VERIFY: sum of all weight_percent values = 100%**

### Step 3: Apply Constraints
From risk_profiles.json for the user's risk score:
- `max_individual_stock`: Maximum % in any single stock
- `min_positions`: Minimum number of positions required
- `max_single_sector`: Maximum % in any sector

### Step 4: Position Sizing (MANDATORY FORMULA)
For EACH stock, compute in this exact order:
```
allocated_amount = (weight_percent / 100) * invested_capital
shares = floor(allocated_amount / current_price)
actual_value = shares * current_price
actual_weight = (actual_value / total_capital) * 100
```

**Example** (total_capital=$10000, invested_capital=$9300, 5 equal-weight stocks):
- Each stock weight_percent = 20%
- Each allocated_amount = 0.20 * $9300 = $1860
- For a $165 stock: shares = floor($1860 / $165) = 11, actual_value = 11 * $165 = $1815

### Step 5: Recalculate Actual Cash Reserve
After computing all positions, recalculate cash to absorb rounding leftovers:
```
actual_total_invested = sum(actual_value for all positions)
actual_cash_reserve = total_capital - actual_total_invested
```
Use `actual_cash_reserve` (not `cash_reserve_amount`) in the output. This ensures:
**stocks + cash = total_capital exactly**

**VERIFY before output:**
- actual_total_invested + actual_cash_reserve == total_capital  (must be exact)
- Each weight in output = actual_value / total_capital * 100

### Step 6: Correlation Check
Use `calculate_correlation_matrix` to verify diversification:
- Flag any pair with correlation > 0.8
- Consider reducing allocation to highly correlated pairs

## Allocation Rules by Risk Profile
- Ultra Conservative (1-2): Max 5% per stock, heavy defensive
- Conservative (3-4): Max 7% per stock, balanced defensive
- Moderate (5-6): Max 10% per stock, balanced
- Growth (7-8): Max 15% per stock, growth tilt
- Aggressive (9-10): Max 20% per stock, high conviction

## Output Format
```json
{
  "portfolio": {
    "total_capital": <number>,
    "currency": "USD",
    "cash_reserve": {
      "amount": <actual_cash_reserve = total_capital - sum(actual position values)>,
      "percentage": <actual_cash_reserve / total_capital * 100>
    },
    "invested_capital": <sum of all actual position values>,
    "positions": [
      {
        "symbol": "<ticker>",
        "name": "<company>",
        "sector": "<sector>",
        "shares": <integer — floor(allocated_amount / price)>,
        "price": <current price>,
        "value": <shares * price>,
        "weight": <(value / total_capital) * 100>,
        "allocation_rationale": "<why this weight>"
      }
    ],
    "sector_allocation": {
      "<sector>": <percentage>
    },
    "portfolio_characteristics": {
      "weighted_beta": <number>,
      "weighted_dividend_yield": <number>,
      "number_of_positions": <number>,
      "largest_position": <percentage>,
      "defensive_allocation": <percentage>,
      "growth_allocation": <percentage>
    },
    "diversification_check": {
      "sector_concentration_ok": <boolean>,
      "position_size_ok": <boolean>,
      "correlation_ok": <boolean>,
      "issues": ["<any issues found>"]
    },
    "construction_notes": "<explanation of allocation decisions>"
  }
}
```"""

portfolio_construction_agent = LlmAgent(
    name="portfolio_construction_agent",
    model="gemini-2.0-flash",
    instruction=PORTFOLIO_CONSTRUCTION_INSTRUCTION,
    description="Allocates capital to stocks with proper diversification",
    tools=[
        get_risk_profile_config,
        get_historical_prices,
        calculate_correlation_matrix,
        calculate_portfolio_volatility,
        calculate_portfolio_return
    ],
    output_key="portfolio"
)
