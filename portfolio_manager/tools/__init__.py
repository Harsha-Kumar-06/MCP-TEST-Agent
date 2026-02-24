"""
Portfolio Manager Tools

This module contains utility functions and API wrappers for:
- Stock market data retrieval (Alpha Vantage)
- Financial calculations (Sharpe ratio, volatility, etc.)
- Macroeconomic indicator analysis
"""

from .stock_api import (
    get_stock_quote,
    get_company_fundamentals,
    get_technical_indicators,
    get_historical_prices,
    get_sector_performance,
    search_stocks,
)

from .calculations import (
    calculate_sharpe_ratio,
    calculate_portfolio_volatility,
    calculate_correlation_matrix,
    calculate_max_drawdown,
    calculate_beta,
    calculate_portfolio_return,
)

from .macro_data import (
    get_economic_indicators,
    calculate_market_outlook_score,
)

__all__ = [
    # Stock API
    "get_stock_quote",
    "get_company_fundamentals",
    "get_technical_indicators",
    "get_historical_prices",
    "get_sector_performance",
    "search_stocks",
    # Calculations
    "calculate_sharpe_ratio",
    "calculate_portfolio_volatility",
    "calculate_correlation_matrix",
    "calculate_max_drawdown",
    "calculate_beta",
    "calculate_portfolio_return",
    # Macro Data
    "get_economic_indicators",
    "calculate_market_outlook_score",
]
