"""
Financial Calculations Module

This module provides mathematical functions for portfolio analysis including:
- Risk metrics (Sharpe ratio, volatility, beta, max drawdown)
- Return calculations
- Correlation analysis for diversification
"""

import statistics
from typing import Optional


def calculate_sharpe_ratio(
    returns: list[float],
    risk_free_rate: float = 0.05
) -> dict:
    """
    Calculate the Sharpe Ratio for a portfolio or stock.
    
    The Sharpe Ratio measures risk-adjusted return. Higher values indicate
    better risk-adjusted performance.
    
    Formula: (Portfolio Return - Risk Free Rate) / Portfolio Std Dev
    
    Args:
        returns: List of periodic returns (daily or monthly)
        risk_free_rate: Annual risk-free rate (default: 5% / 0.05)
    
    Returns:
        dict: Sharpe ratio analysis including:
            - sharpe_ratio: The calculated ratio
            - annualized_return: Annualized portfolio return
            - annualized_volatility: Annualized standard deviation
            - interpretation: Qualitative assessment
    
    Interpretation:
        - < 0: Bad (losing money or underperforming risk-free)
        - 0-1: Adequate (needs improvement)
        - 1-2: Good (solid risk-adjusted returns)
        - 2-3: Very Good (excellent performance)
        - > 3: Excellent (exceptional, verify data)
    
    Example:
        >>> calculate_sharpe_ratio([0.01, 0.02, -0.01, 0.015], 0.05)
        {'sharpe_ratio': 1.25, 'interpretation': 'good'}
    """
    if not returns or len(returns) < 2:
        return {
            "sharpe_ratio": 0,
            "error": "Insufficient data: need at least 2 return periods",
            "interpretation": "insufficient_data"
        }
    
    # Calculate mean return and standard deviation
    mean_return = statistics.mean(returns)
    std_dev = statistics.stdev(returns)
    
    if std_dev == 0:
        return {
            "sharpe_ratio": 0,
            "error": "Zero volatility detected",
            "interpretation": "invalid"
        }
    
    # Assume daily returns, annualize (252 trading days)
    annualized_return = mean_return * 252
    annualized_volatility = std_dev * (252 ** 0.5)
    
    # Calculate Sharpe Ratio
    sharpe = (annualized_return - risk_free_rate) / annualized_volatility
    
    # Interpretation
    if sharpe < 0:
        interpretation = "poor"
    elif sharpe < 1:
        interpretation = "adequate"
    elif sharpe < 2:
        interpretation = "good"
    elif sharpe < 3:
        interpretation = "very_good"
    else:
        interpretation = "excellent"
    
    return {
        "sharpe_ratio": round(sharpe, 3),
        "mean_daily_return": round(mean_return, 6),
        "annualized_return": round(annualized_return, 4),
        "annualized_volatility": round(annualized_volatility, 4),
        "risk_free_rate": risk_free_rate,
        "interpretation": interpretation,
        "data_points": len(returns)
    }


def calculate_portfolio_volatility(
    weights: list[float],
    returns_matrix: list[list[float]]
) -> dict:
    """
    Calculate portfolio volatility using weighted returns.
    
    Args:
        weights: List of portfolio weights (should sum to 1.0)
        returns_matrix: 2D list where each inner list is returns for one stock
    
    Returns:
        dict: Volatility metrics including:
            - portfolio_volatility: Daily portfolio volatility
            - annualized_volatility: Annualized volatility
            - individual_volatilities: Volatility of each component
    
    Example:
        >>> weights = [0.5, 0.5]
        >>> returns = [[0.01, 0.02], [0.015, -0.01]]  # 2 stocks, 2 days
        >>> calculate_portfolio_volatility(weights, returns)
        {'portfolio_volatility': 0.012, 'annualized_volatility': 0.19}
    """
    if not weights or not returns_matrix:
        return {
            "portfolio_volatility": 0,
            "error": "Missing weights or returns data"
        }
    
    if abs(sum(weights) - 1.0) > 0.01:
        return {
            "portfolio_volatility": 0,
            "error": f"Weights must sum to 1.0, got {sum(weights)}"
        }
    
    if len(weights) != len(returns_matrix):
        return {
            "portfolio_volatility": 0,
            "error": "Number of weights must match number of return series"
        }
    
    # Calculate individual volatilities
    individual_vols = []
    for returns in returns_matrix:
        if len(returns) > 1:
            vol = statistics.stdev(returns)
        else:
            vol = 0
        individual_vols.append(vol)
    
    # Calculate portfolio returns
    min_length = min(len(r) for r in returns_matrix)
    portfolio_returns = []
    
    for i in range(min_length):
        weighted_return = sum(
            weights[j] * returns_matrix[j][i] 
            for j in range(len(weights))
        )
        portfolio_returns.append(weighted_return)
    
    # Calculate portfolio volatility
    if len(portfolio_returns) > 1:
        portfolio_vol = statistics.stdev(portfolio_returns)
    else:
        portfolio_vol = 0
    
    annualized_vol = portfolio_vol * (252 ** 0.5)
    
    return {
        "portfolio_volatility": round(portfolio_vol, 6),
        "annualized_volatility": round(annualized_vol, 4),
        "individual_volatilities": [round(v, 6) for v in individual_vols],
        "individual_annualized": [round(v * (252 ** 0.5), 4) for v in individual_vols],
        "data_points": min_length,
        "diversification_benefit": round(
            sum(w * v for w, v in zip(weights, individual_vols)) - portfolio_vol, 6
        ) if individual_vols else 0
    }


def calculate_correlation_matrix(
    returns_dict: dict[str, list[float]]
) -> dict:
    """
    Calculate correlation matrix between multiple stocks.
    
    Used for portfolio diversification analysis. Lower correlations
    between stocks indicate better diversification potential.
    
    Args:
        returns_dict: Dictionary mapping symbol to list of returns
            Example: {"AAPL": [0.01, 0.02], "MSFT": [0.015, 0.01]}
    
    Returns:
        dict: Correlation analysis including:
            - correlations: Pairwise correlation matrix
            - average_correlation: Mean correlation across all pairs
            - high_correlations: Pairs with correlation > 0.7
            - diversification_score: 0-100 score (higher = better diversified)
    
    Example:
        >>> returns = {"AAPL": [0.01, 0.02, 0.015], "MSFT": [0.012, 0.018, 0.01]}
        >>> calculate_correlation_matrix(returns)
        {'correlations': {'AAPL-MSFT': 0.85}, 'diversification_score': 65}
    """
    symbols = list(returns_dict.keys())
    
    if len(symbols) < 2:
        return {
            "correlations": {},
            "error": "Need at least 2 stocks for correlation analysis"
        }
    
    # Ensure all return series have the same length
    min_length = min(len(returns_dict[s]) for s in symbols)
    
    if min_length < 3:
        return {
            "correlations": {},
            "error": "Need at least 3 data points for correlation"
        }
    
    # Trim all series to same length
    trimmed = {s: returns_dict[s][:min_length] for s in symbols}
    
    # Calculate pairwise correlations
    correlations = {}
    correlation_values = []
    
    for i, sym1 in enumerate(symbols):
        for sym2 in symbols[i+1:]:
            corr = _pearson_correlation(trimmed[sym1], trimmed[sym2])
            key = f"{sym1}-{sym2}"
            correlations[key] = round(corr, 3)
            correlation_values.append(corr)
    
    # Identify highly correlated pairs (potential diversification issues)
    high_correlations = {k: v for k, v in correlations.items() if v > 0.7}
    
    # Calculate diversification score (0-100)
    # Lower average correlation = higher score
    avg_corr = statistics.mean(correlation_values) if correlation_values else 0
    diversification_score = max(0, min(100, int((1 - avg_corr) * 100)))
    
    return {
        "symbols": symbols,
        "correlations": correlations,
        "average_correlation": round(avg_corr, 3),
        "high_correlations": high_correlations,
        "diversification_score": diversification_score,
        "interpretation": _interpret_diversification(diversification_score),
        "data_points": min_length
    }


def _pearson_correlation(x: list[float], y: list[float]) -> float:
    """Calculate Pearson correlation coefficient between two series."""
    n = len(x)
    if n != len(y) or n < 2:
        return 0
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)
    
    denominator = (var_x * var_y) ** 0.5
    
    if denominator == 0:
        return 0
    
    return numerator / denominator


def _interpret_diversification(score: int) -> str:
    """Interpret diversification score."""
    if score >= 80:
        return "excellent_diversification"
    elif score >= 60:
        return "good_diversification"
    elif score >= 40:
        return "moderate_diversification"
    else:
        return "poor_diversification"


def calculate_max_drawdown(prices: list[float]) -> dict:
    """
    Calculate maximum drawdown from a price series.
    
    Maximum drawdown measures the largest peak-to-trough decline,
    representing the worst-case loss scenario.
    
    Args:
        prices: List of prices (chronological order, oldest first)
    
    Returns:
        dict: Drawdown analysis including:
            - max_drawdown: Maximum percentage drawdown
            - max_drawdown_duration: Number of periods in drawdown
            - recovery_time: Periods to recover from max drawdown
            - current_drawdown: Current drawdown from peak
    
    Example:
        >>> prices = [100, 110, 95, 105, 90, 100]
        >>> calculate_max_drawdown(prices)
        {'max_drawdown': -0.182, 'interpretation': 'moderate_risk'}
    """
    if not prices or len(prices) < 2:
        return {
            "max_drawdown": 0,
            "error": "Need at least 2 price points"
        }
    
    peak = prices[0]
    max_drawdown = 0
    max_drawdown_start = 0
    max_drawdown_end = 0
    current_drawdown_start = 0
    
    for i, price in enumerate(prices):
        if price > peak:
            peak = price
            current_drawdown_start = i
        
        drawdown = (price - peak) / peak
        
        if drawdown < max_drawdown:
            max_drawdown = drawdown
            max_drawdown_start = current_drawdown_start
            max_drawdown_end = i
    
    # Current drawdown
    current_peak = max(prices)
    current_drawdown = (prices[-1] - current_peak) / current_peak
    
    # Interpret risk
    if max_drawdown > -0.1:
        interpretation = "low_risk"
    elif max_drawdown > -0.2:
        interpretation = "moderate_risk"
    elif max_drawdown > -0.3:
        interpretation = "high_risk"
    else:
        interpretation = "very_high_risk"
    
    return {
        "max_drawdown": round(max_drawdown, 4),
        "max_drawdown_percent": f"{max_drawdown * 100:.2f}%",
        "max_drawdown_start_idx": max_drawdown_start,
        "max_drawdown_end_idx": max_drawdown_end,
        "max_drawdown_duration": max_drawdown_end - max_drawdown_start,
        "current_drawdown": round(current_drawdown, 4),
        "current_drawdown_percent": f"{current_drawdown * 100:.2f}%",
        "interpretation": interpretation,
        "data_points": len(prices)
    }


def calculate_beta(
    stock_returns: list[float],
    benchmark_returns: list[float]
) -> dict:
    """
    Calculate stock beta relative to a benchmark.
    
    Beta measures a stock's volatility relative to the market.
    - Beta = 1: Moves with the market
    - Beta > 1: More volatile than market
    - Beta < 1: Less volatile than market
    - Beta < 0: Moves opposite to market
    
    Args:
        stock_returns: List of stock returns
        benchmark_returns: List of benchmark (e.g., S&P 500) returns
    
    Returns:
        dict: Beta analysis including:
            - beta: Calculated beta value
            - alpha: Jensen's alpha (excess return)
            - r_squared: Correlation with benchmark
            - interpretation: Risk assessment
    
    Example:
        >>> stock = [0.02, 0.01, -0.01, 0.03]
        >>> market = [0.01, 0.005, -0.005, 0.02]
        >>> calculate_beta(stock, market)
        {'beta': 1.5, 'interpretation': 'aggressive'}
    """
    if len(stock_returns) != len(benchmark_returns):
        min_len = min(len(stock_returns), len(benchmark_returns))
        stock_returns = stock_returns[:min_len]
        benchmark_returns = benchmark_returns[:min_len]
    
    if len(stock_returns) < 3:
        return {
            "beta": 1.0,
            "error": "Insufficient data for beta calculation"
        }
    
    # Calculate covariance and variance
    n = len(stock_returns)
    mean_stock = sum(stock_returns) / n
    mean_benchmark = sum(benchmark_returns) / n
    
    covariance = sum(
        (stock_returns[i] - mean_stock) * (benchmark_returns[i] - mean_benchmark)
        for i in range(n)
    ) / (n - 1)
    
    variance_benchmark = sum(
        (benchmark_returns[i] - mean_benchmark) ** 2
        for i in range(n)
    ) / (n - 1)
    
    if variance_benchmark == 0:
        return {
            "beta": 1.0,
            "error": "Zero variance in benchmark"
        }
    
    # Calculate beta
    beta = covariance / variance_benchmark
    
    # Calculate alpha (Jensen's Alpha)
    # Annualized: alpha = avg_stock_return - (risk_free + beta * (market_return - risk_free))
    risk_free_daily = 0.05 / 252  # Assume 5% annual risk-free rate
    alpha = (mean_stock - risk_free_daily) - beta * (mean_benchmark - risk_free_daily)
    annualized_alpha = alpha * 252
    
    # Calculate R-squared
    correlation = _pearson_correlation(stock_returns, benchmark_returns)
    r_squared = correlation ** 2
    
    # Interpret beta
    if beta < 0.5:
        interpretation = "defensive"
    elif beta < 1.0:
        interpretation = "conservative"
    elif beta < 1.5:
        interpretation = "moderate"
    else:
        interpretation = "aggressive"
    
    return {
        "beta": round(beta, 3),
        "alpha_daily": round(alpha, 6),
        "alpha_annualized": round(annualized_alpha, 4),
        "r_squared": round(r_squared, 3),
        "correlation": round(correlation, 3),
        "interpretation": interpretation,
        "data_points": n
    }


def calculate_portfolio_return(
    weights: list[float],
    returns: list[float]
) -> dict:
    """
    Calculate weighted portfolio return.
    
    Args:
        weights: List of allocation weights (should sum to 1.0)
        returns: List of individual asset returns
    
    Returns:
        dict: Portfolio return metrics
    
    Example:
        >>> weights = [0.6, 0.4]
        >>> returns = [0.10, 0.05]  # 10% and 5% returns
        >>> calculate_portfolio_return(weights, returns)
        {'portfolio_return': 0.08}  # 8% weighted return
    """
    if len(weights) != len(returns):
        return {
            "portfolio_return": 0,
            "error": "Weights and returns must have same length"
        }
    
    if abs(sum(weights) - 1.0) > 0.01:
        return {
            "portfolio_return": 0,
            "error": f"Weights must sum to 1.0, got {sum(weights)}"
        }
    
    portfolio_return = sum(w * r for w, r in zip(weights, returns))
    
    # Calculate contribution from each asset
    contributions = [
        {"weight": round(w, 4), "return": round(r, 4), "contribution": round(w * r, 6)}
        for w, r in zip(weights, returns)
    ]
    
    return {
        "portfolio_return": round(portfolio_return, 6),
        "portfolio_return_percent": f"{portfolio_return * 100:.2f}%",
        "contributions": contributions
    }


def calculate_var(
    returns: list[float],
    confidence_level: float = 0.95,
    portfolio_value: float = 10000.0
) -> dict:
    """
    Calculate Value at Risk (VaR) using historical simulation.
    
    VaR estimates the potential loss over a specific time period
    at a given confidence level.
    
    Args:
        returns: List of historical returns
        confidence_level: Confidence level (default: 95%)
        portfolio_value: Current portfolio value
    
    Returns:
        dict: VaR analysis including:
            - var_percent: VaR as percentage
            - var_dollar: VaR in dollar terms
            - interpretation: Risk assessment
    
    Example:
        >>> returns = [0.01, -0.02, 0.005, -0.03, 0.02]
        >>> calculate_var(returns, 0.95, 10000)
        {'var_percent': -0.025, 'var_dollar': -250}
    """
    if not returns or len(returns) < 10:
        return {
            "var_percent": 0,
            "error": "Need at least 10 data points for VaR"
        }
    
    # Sort returns to find percentile
    sorted_returns = sorted(returns)
    
    # Find the VaR percentile
    percentile_idx = int((1 - confidence_level) * len(sorted_returns))
    var_percent = sorted_returns[percentile_idx]
    var_dollar = portfolio_value * var_percent
    
    # Also calculate Expected Shortfall (CVaR)
    cvar_returns = sorted_returns[:percentile_idx + 1]
    cvar_percent = statistics.mean(cvar_returns) if cvar_returns else var_percent
    cvar_dollar = portfolio_value * cvar_percent
    
    return {
        "confidence_level": confidence_level,
        "var_percent": round(var_percent, 4),
        "var_dollar": round(var_dollar, 2),
        "cvar_percent": round(cvar_percent, 4),
        "cvar_dollar": round(cvar_dollar, 2),
        "interpretation": f"There is a {(1-confidence_level)*100:.0f}% chance of losing more than ${abs(var_dollar):.2f} ({abs(var_percent)*100:.2f}%) in a single day",
        "data_points": len(returns)
    }
