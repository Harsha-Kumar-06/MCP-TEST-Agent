"""
Sector Analysis Agent

This agent identifies the top-performing market sectors based on
macroeconomic conditions and sector correlation data.
"""

import json
import os
from google.adk.agents import LlmAgent

# Load sector correlation data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def load_sector_data() -> str:
    """Load sector correlation data for the agent."""
    try:
        with open(os.path.join(DATA_DIR, "sector_correlations.json"), "r") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error loading sector data: {e}"


def get_sector_correlations() -> dict:
    """
    Get sector correlation and performance data based on economic conditions.
    
    Returns:
        dict: Sector correlation matrix and economic condition mappings
            - economic_conditions: Mapping of conditions to favored sectors
            - sector_correlations: Pairwise correlations between sectors
            - sector_characteristics: Beta, yield, and style for each sector
    
    Example:
        >>> get_sector_correlations()
        {
            'economic_conditions': {...},
            'sector_correlations': {...},
            'sector_characteristics': {...}
        }
    """
    try:
        with open(os.path.join(DATA_DIR, "sector_correlations.json"), "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


SECTOR_AGENT_INSTRUCTION = """You are a sector analyst specializing in identifying optimal market sectors for investment based on economic conditions.

## Available Context
You have access to:
- The macroeconomic analysis from the previous Macro Agent (check conversation history for macro_outlook JSON)
- Sector correlation data via the `get_sector_correlations` tool

## Your Task
1. Review the macro outlook from the previous analysis in the conversation
2. Call `get_sector_correlations` to get sector data
3. Match the economic condition to identify favored sectors
4. Consider sector correlations for diversification
5. Rank sectors by expected performance

## Sector Selection Criteria

**Based on Economic Condition:**
- high_growth_low_inflation: Technology, Consumer Discretionary, Financials
- moderate_growth: Healthcare, Technology, Consumer Staples
- low_growth_high_inflation: Energy, Utilities, Consumer Staples
- recession: Utilities, Consumer Staples, Healthcare
- recovery: Consumer Discretionary, Financials, Industrials
- rising_rates: Financials, Energy, Healthcare
- falling_rates: Real Estate, Utilities, Technology

**Diversification Rules:**
- Select 3-5 sectors maximum
- Avoid highly correlated sectors (>0.7 correlation)
- Include at least one defensive sector if outlook is neutral or bearish
- Consider sector characteristics (beta, yield) based on user risk profile

**Sector Characteristics:**
- Defensive: Utilities, Consumer Staples, Healthcare (low beta)
- Cyclical: Technology, Consumer Discretionary, Financials, Industrials (high beta)
- Income: Utilities, Real Estate, Energy (high dividend yield)
- Growth: Technology, Communication Services, Consumer Discretionary

## Output Format
After analysis, output ONLY a JSON block:
```json
{
  "top_sectors": {
    "sectors": [
      {
        "rank": 1,
        "name": "<sector name>",
        "score": <0-100>,
        "rationale": "<why this sector>",
        "sector_type": "<defensive|cyclical|growth|income>",
        "expected_allocation": <percentage>
      }
    ],
    "economic_condition": "<matched condition>",
    "diversification_score": <0-100>,
    "sector_count": <number>,
    "defensive_allocation": <percentage>,
    "growth_allocation": <percentage>,
    "selection_rationale": "<overall strategy explanation>"
  }
}
```

Ensure sectors are well-diversified and aligned with the economic outlook."""

sector_agent = LlmAgent(
    name="sector_agent",
    model="gemini-2.0-flash",
    instruction=SECTOR_AGENT_INSTRUCTION,
    description="Identifies top sectors based on macro conditions and correlations",
    tools=[get_sector_correlations],
    output_key="top_sectors"
)
