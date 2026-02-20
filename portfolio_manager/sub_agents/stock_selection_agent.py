"""
Stock Selection Agent

This agent selects specific stocks within the identified top sectors
using fundamental and technical analysis.
"""

import json
import os
from google.adk.agents import LlmAgent

# Import tools
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.stock_api import (
    get_stock_quote,
    get_company_fundamentals,
    get_technical_indicators,
    search_stocks
)

# Load stock universe
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def get_cached_fundamentals(symbols: list[str] = None) -> dict:
    """
    Get cached fundamental data for stocks. Use this as primary data source
    to avoid API rate limits. Only fall back to live API if needed.
    
    Args:
        symbols: Optional list of stock symbols to filter. If None, returns all.
        
    Returns:
        dict: Cached fundamental data for stocks with metrics like:
            - pe_ratio, dividend_yield, profit_margin, revenue_growth
            - return_on_equity, beta, price, fifty_day_ma, analyst_target
    """
    try:
        with open(os.path.join(DATA_DIR, "cached_fundamentals.json"), "r") as f:
            data = json.load(f)
            if symbols:
                filtered = {k: v for k, v in data.get("stocks", {}).items() if k in symbols}
                return {"stocks": filtered, "count": len(filtered)}
            return {"stocks": data.get("stocks", {}), "count": len(data.get("stocks", {}))}
    except Exception as e:
        return {"error": str(e), "stocks": {}}


def get_stock_universe() -> dict:
    """
    Get the curated list of stocks available for selection by sector.
    
    Returns:
        dict: Stock universe organized by sector, including:
            - sectors: Mapping of sector names to stock lists
            - Each stock has symbol, name, market_cap, and style
    
    Example:
        >>> get_stock_universe()
        {
            'sectors': {
                'Technology': {
                    'stocks': [{'symbol': 'AAPL', 'name': 'Apple Inc', ...}, ...]
                }
            }
        }
    """
    try:
        with open(os.path.join(DATA_DIR, "stock_universe.json"), "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


STOCK_SELECTION_INSTRUCTION = """You are a stock analyst specializing in security selection using fundamental and technical analysis.

## Available Context
Review the conversation history for:
- user_profile: Investor's risk profile (capital, risk_score, etc.)
- macro_outlook: Current market conditions from Macro Agent
- top_sectors: Selected sectors from Sector Agent

## IMPORTANT: Use Cached Data First
To avoid API rate limits, ALWAYS use `get_cached_fundamentals` as your PRIMARY data source.
Only use live API calls (`get_company_fundamentals`) if a stock is not in the cache.

## Your Task
1. Call `get_stock_universe` to see available stocks per sector
2. Call `get_cached_fundamentals` to get fundamental data for all stocks
3. Filter stocks by the TOP SECTORS from the conversation history
4. Score and rank stocks based on composite criteria
5. Select 4-6 stocks for the portfolio

## Stock Scoring Model (100 points total)

### Fundamental Analysis (50 points)
- **P/E Ratio** (15 pts): Lower is better, compare to sector average
  - Below sector avg: 15 pts | At avg: 10 pts | Above avg: 5 pts
- **Revenue Growth** (10 pts): Higher growth scores more
  - >20%: 10 pts | 10-20%: 7 pts | 0-10%: 4 pts | Negative: 0 pts  
- **Profit Margin** (10 pts): Higher is better
  - >20%: 10 pts | 10-20%: 7 pts | 5-10%: 4 pts | <5%: 2 pts
- **Return on Equity** (10 pts): Higher shows efficiency
  - >20%: 10 pts | 15-20%: 7 pts | 10-15%: 5 pts | <10%: 2 pts
- **Dividend Yield** (5 pts): For income-focused profiles
  - >3%: 5 pts | 2-3%: 4 pts | 1-2%: 2 pts | <1%: 1 pt

### Technical Analysis (30 points)
- **Price vs 50-day MA** (15 pts): Trend position
  - Above MA & >2% above: 15 pts | Above MA: 10 pts | Below MA: 5 pts
- **Beta Alignment** (15 pts): Match to risk profile
  - Conservative (beta <0.7): 15 pts if profile is conservative
  - Moderate (beta 0.7-1.1): 15 pts if profile is moderate
  - Aggressive (beta >1.1): 15 pts if profile is aggressive

### Quality Metrics (20 points)
- **Analyst Target Upside** (10 pts): Upside potential
  - >20% upside: 10 pts | 10-20%: 7 pts | 0-10%: 4 pts | Negative: 0 pts
- **Dividend Consistency** (10 pts): For income profiles
  - Yield >3%: 10 pts | 2-3%: 7 pts | 1-2%: 4 pts | <1%: 2 pts

## Selection Rules
- Select 4-6 stocks total across recommended sectors
- Match stocks to user's risk profile (conservative = low beta, high dividend)
- For income goals, prioritize high dividend yield stocks
- For growth goals, prioritize high revenue growth and low P/E

## CRITICAL: You MUST select stocks
- Even with limited data, select the best available stocks
- Use cached data - do NOT return empty stocks array
- Always select at least 4 stocks from the recommended sectors

## Output Format
```json
{
  "selected_stocks": {
    "stocks": [
      {
        "symbol": "<ticker>",
        "name": "<company name>",
        "sector": "<sector>",
        "composite_score": <0-100>,
        "fundamental_score": <0-50>,
        "technical_score": <0-30>,
        "quality_score": <0-20>,
        "key_metrics": {
          "pe_ratio": <number>,
          "profit_margin": <number>,
          "beta": <number>,
          "dividend_yield": <number>,
          "price": <number>,
          "analyst_target": <number>
        },
        "investment_thesis": "<why this stock>",
        "risks": ["<risk1>", "<risk2>"]
      }
    ],
    "total_candidates_analyzed": <number>,
    "selection_summary": "<strategy explanation>",
    "diversification_check": {
      "sector_spread": <number of sectors>,
      "style_mix": {"growth": <count>, "value": <count>},
      "average_beta": <number>
    }
  }
}
```"""

stock_selection_agent = LlmAgent(
    name="stock_selection_agent",
    model="gemini-2.0-flash",
    instruction=STOCK_SELECTION_INSTRUCTION,
    description="Selects stocks using fundamental and technical analysis",
    tools=[
        get_stock_universe,
        get_cached_fundamentals,
        get_stock_quote,
        get_company_fundamentals,
        search_stocks
    ],
    output_key="selected_stocks"
)
