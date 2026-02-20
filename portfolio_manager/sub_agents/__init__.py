"""
Portfolio Manager Sub-Agents

This module exports all sub-agents used in the portfolio management pipeline:

1. Macro Agent - Analyzes macroeconomic conditions
2. Sector Agent - Identifies top-performing sectors
3. Stock Selection Agent - Selects specific stocks
4. Portfolio Construction Agent - Allocates capital
5. Performance Agent - Calculates performance metrics
6. Backtest Agent - Validates with historical data
7. Report Synthesizer Agent - Generates final report

Note: User profile collection is handled by the root agent directly.
"""

from .macro_agent import macro_agent
from .sector_agent import sector_agent
from .stock_selection_agent import stock_selection_agent
from .portfolio_construction_agent import portfolio_construction_agent
from .performance_agent import performance_agent
from .backtest_agent import backtest_agent
from .report_synthesizer_agent import report_synthesizer_agent

__all__ = [
    "macro_agent",
    "sector_agent",
    "stock_selection_agent",
    "portfolio_construction_agent",
    "performance_agent",
    "backtest_agent",
    "report_synthesizer_agent",
]
