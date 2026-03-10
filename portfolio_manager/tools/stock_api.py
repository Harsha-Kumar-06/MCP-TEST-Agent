"""
Stock Market Data API Tools

This module provides functions to fetch real stock market data using Alpha Vantage API
with yfinance as a fallback. Includes rate limiting to respect API constraints.

Alpha Vantage Free Tier: 5 API calls per minute, 500 calls per day
"""

import os
import time
import json
from functools import wraps
from typing import Optional
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()

# Configuration
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# Rate limiting configuration
RATE_LIMIT_CALLS = 5
RATE_LIMIT_PERIOD = 60  # seconds
_call_timestamps: list[float] = []


def _safe_float(value, default: float = 0.0) -> float:
    """Convert value to float, returning default for None / empty / non-numeric strings."""
    try:
        return float(value) if value not in (None, "", "None", "N/A", "-") else default
    except (ValueError, TypeError):
        return default


def _safe_int(value, default: int = 0) -> int:
    """Convert value to int, returning default for None / empty / non-numeric strings."""
    try:
        return int(float(value)) if value not in (None, "", "None", "N/A", "-") else default
    except (ValueError, TypeError):
        return default


def _rate_limit(func):
    """
    Decorator to enforce rate limiting (5 calls per minute for Alpha Vantage free tier).
    Implements a sliding window rate limiter.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _call_timestamps
        now = time.time()
        
        # Remove timestamps older than the rate limit period
        _call_timestamps = [ts for ts in _call_timestamps if now - ts < RATE_LIMIT_PERIOD]
        
        # Check if we've exceeded the rate limit
        if len(_call_timestamps) >= RATE_LIMIT_CALLS:
            # Wait until the oldest call expires
            sleep_time = RATE_LIMIT_PERIOD - (now - _call_timestamps[0]) + 1
            if sleep_time > 0:
                time.sleep(sleep_time)
                _call_timestamps = []
        
        # Record this call
        _call_timestamps.append(time.time())
        
        return func(*args, **kwargs)
    
    return wrapper


def _make_alpha_vantage_request(params: dict) -> dict:
    """Make a request to Alpha Vantage API with error handling."""
    params["apikey"] = ALPHA_VANTAGE_API_KEY
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(ALPHA_VANTAGE_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check for API error messages
            if "Error Message" in data:
                return {"error": data["Error Message"]}
            if "Note" in data:  # Rate limit exceeded message
                return {"error": f"Rate limit exceeded: {data['Note']}"}
            if "Information" in data:
                return {"error": data["Information"]}
            
            return data
    except httpx.HTTPError as e:
        return {"error": f"HTTP error: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from API"}


@_rate_limit
def get_stock_quote(symbol: str) -> dict:
    """
    Get real-time stock quote data for a given symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
    
    Returns:
        dict: Stock quote data including:
            - symbol: Stock ticker
            - price: Current price
            - change: Price change
            - change_percent: Percentage change
            - volume: Trading volume
            - latest_trading_day: Date of last trade
            - previous_close: Previous closing price
            - open: Opening price
            - high: Day high
            - low: Day low
    
    Example:
        >>> get_stock_quote("AAPL")
        {'symbol': 'AAPL', 'price': 178.50, 'change': 2.30, ...}
    """
    data = _make_alpha_vantage_request({
        "function": "GLOBAL_QUOTE",
        "symbol": symbol
    })
    
    if "error" in data:
        return data
    
    quote = data.get("Global Quote", {})
    
    if not quote:
        return {"error": f"No quote data found for symbol: {symbol}"}
    
    return {
        "symbol": quote.get("01. symbol", symbol),
        "price": _safe_float(quote.get("05. price")),
        "change": _safe_float(quote.get("09. change")),
        "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
        "volume": _safe_int(quote.get("06. volume")),
        "latest_trading_day": quote.get("07. latest trading day", ""),
        "previous_close": _safe_float(quote.get("08. previous close")),
        "open": _safe_float(quote.get("02. open")),
        "high": _safe_float(quote.get("03. high")),
        "low": _safe_float(quote.get("04. low"))
    }


@_rate_limit
def get_company_fundamentals(symbol: str) -> dict:
    """
    Get fundamental data for a company including financial ratios and metrics.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
    
    Returns:
        dict: Company fundamentals including:
            - symbol: Stock ticker
            - name: Company name
            - sector: Business sector
            - industry: Specific industry
            - market_cap: Market capitalization
            - pe_ratio: Price-to-earnings ratio
            - peg_ratio: Price/Earnings to Growth ratio
            - book_value: Book value per share
            - dividend_yield: Dividend yield percentage
            - eps: Earnings per share
            - revenue_ttm: Trailing twelve months revenue
            - profit_margin: Profit margin percentage
            - beta: Stock beta (volatility measure)
            - 52_week_high: 52-week high price
            - 52_week_low: 52-week low price
    
    Example:
        >>> get_company_fundamentals("AAPL")
        {'symbol': 'AAPL', 'name': 'Apple Inc', 'pe_ratio': 28.5, ...}
    """
    data = _make_alpha_vantage_request({
        "function": "OVERVIEW",
        "symbol": symbol
    })
    
    if "error" in data:
        return data
    
    if not data or "Symbol" not in data:
        return {"error": f"No fundamental data found for symbol: {symbol}"}
    
    def safe_float(value, default=0.0):
        try:
            return float(value) if value and value != "None" else default
        except (ValueError, TypeError):
            return default
    
    def safe_int(value, default=0):
        try:
            return int(value) if value and value != "None" else default
        except (ValueError, TypeError):
            return default
    
    return {
        "symbol": data.get("Symbol", symbol),
        "name": data.get("Name", ""),
        "description": data.get("Description", "")[:200] + "..." if len(data.get("Description", "")) > 200 else data.get("Description", ""),
        "sector": data.get("Sector", ""),
        "industry": data.get("Industry", ""),
        "market_cap": safe_int(data.get("MarketCapitalization")),
        "pe_ratio": safe_float(data.get("PERatio")),
        "peg_ratio": safe_float(data.get("PEGRatio")),
        "book_value": safe_float(data.get("BookValue")),
        "dividend_yield": safe_float(data.get("DividendYield")),
        "eps": safe_float(data.get("EPS")),
        "revenue_ttm": safe_int(data.get("RevenueTTM")),
        "profit_margin": safe_float(data.get("ProfitMargin")),
        "operating_margin": safe_float(data.get("OperatingMarginTTM")),
        "return_on_equity": safe_float(data.get("ReturnOnEquityTTM")),
        "return_on_assets": safe_float(data.get("ReturnOnAssetsTTM")),
        "beta": safe_float(data.get("Beta")),
        "52_week_high": safe_float(data.get("52WeekHigh")),
        "52_week_low": safe_float(data.get("52WeekLow")),
        "50_day_moving_avg": safe_float(data.get("50DayMovingAverage")),
        "200_day_moving_avg": safe_float(data.get("200DayMovingAverage")),
        "analyst_target_price": safe_float(data.get("AnalystTargetPrice")),
        "forward_pe": safe_float(data.get("ForwardPE")),
        "price_to_book": safe_float(data.get("PriceToBookRatio")),
        "price_to_sales": safe_float(data.get("PriceToSalesRatioTTM")),
    }


@_rate_limit
def get_technical_indicators(symbol: str, indicator: str = "RSI", interval: str = "daily", time_period: int = 14) -> dict:
    """
    Get technical indicator data for a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        indicator: Technical indicator type. Supported values:
            - 'RSI': Relative Strength Index (momentum)
            - 'MACD': Moving Average Convergence Divergence (trend)
            - 'SMA': Simple Moving Average
            - 'EMA': Exponential Moving Average
            - 'BBANDS': Bollinger Bands
            - 'STOCH': Stochastic Oscillator
            - 'ADX': Average Directional Index (trend strength)
        interval: Time interval ('daily', 'weekly', 'monthly')
        time_period: Number of periods for calculation (default: 14)
    
    Returns:
        dict: Technical indicator data including:
            - symbol: Stock ticker
            - indicator: Indicator type
            - latest_value: Most recent indicator value
            - values: List of recent values with dates
            - signal: Buy/Sell/Hold signal interpretation
    
    Example:
        >>> get_technical_indicators("AAPL", "RSI")
        {'symbol': 'AAPL', 'indicator': 'RSI', 'latest_value': 55.2, 'signal': 'neutral'}
    """
    indicator = indicator.upper()
    
    # Map indicator to API function
    indicator_functions = {
        "RSI": "RSI",
        "MACD": "MACD",
        "SMA": "SMA",
        "EMA": "EMA",
        "BBANDS": "BBANDS",
        "STOCH": "STOCH",
        "ADX": "ADX"
    }
    
    if indicator not in indicator_functions:
        return {"error": f"Unsupported indicator: {indicator}. Supported: {list(indicator_functions.keys())}"}
    
    params = {
        "function": indicator_functions[indicator],
        "symbol": symbol,
        "interval": interval,
    }
    
    # Add time_period for indicators that need it
    if indicator not in ["MACD"]:
        params["time_period"] = time_period
    
    # Add series_type for indicators that need it
    if indicator in ["RSI", "SMA", "EMA", "BBANDS"]:
        params["series_type"] = "close"
    
    data = _make_alpha_vantage_request(params)
    
    if "error" in data:
        return data
    
    # Find the data key (varies by indicator)
    data_key = None
    for key in data.keys():
        if "Technical Analysis" in key:
            data_key = key
            break
    
    if not data_key:
        return {"error": f"No technical data found for {symbol} with indicator {indicator}"}
    
    tech_data = data[data_key]
    
    # Get the most recent values
    dates = sorted(tech_data.keys(), reverse=True)[:30]
    values = []
    
    for date in dates:
        point = tech_data[date]
        if indicator == "RSI":
            values.append({"date": date, "value": float(point.get("RSI", 0))})
        elif indicator == "MACD":
            values.append({
                "date": date, 
                "macd": float(point.get("MACD", 0)),
                "signal": float(point.get("MACD_Signal", 0)),
                "histogram": float(point.get("MACD_Hist", 0))
            })
        elif indicator in ["SMA", "EMA"]:
            values.append({"date": date, "value": float(point.get(indicator, 0))})
        elif indicator == "BBANDS":
            values.append({
                "date": date,
                "upper": float(point.get("Real Upper Band", 0)),
                "middle": float(point.get("Real Middle Band", 0)),
                "lower": float(point.get("Real Lower Band", 0))
            })
        elif indicator == "STOCH":
            values.append({
                "date": date,
                "slowk": float(point.get("SlowK", 0)),
                "slowd": float(point.get("SlowD", 0))
            })
        elif indicator == "ADX":
            values.append({"date": date, "value": float(point.get("ADX", 0))})
    
    # Generate signal interpretation
    latest = values[0] if values else {}
    signal = _interpret_indicator(indicator, latest)
    
    return {
        "symbol": symbol,
        "indicator": indicator,
        "interval": interval,
        "time_period": time_period,
        "latest_value": latest,
        "values": values[:10],  # Return last 10 values
        "signal": signal
    }


def _interpret_indicator(indicator: str, latest: dict) -> str:
    """Interpret technical indicator values into trading signals."""
    if not latest:
        return "insufficient_data"
    
    if indicator == "RSI":
        rsi = latest.get("value", 50)
        if rsi > 70:
            return "overbought_sell"
        elif rsi < 30:
            return "oversold_buy"
        else:
            return "neutral"
    
    elif indicator == "MACD":
        histogram = latest.get("histogram", 0)
        if histogram > 0:
            return "bullish"
        elif histogram < 0:
            return "bearish"
        else:
            return "neutral"
    
    elif indicator == "STOCH":
        slowk = latest.get("slowk", 50)
        if slowk > 80:
            return "overbought_sell"
        elif slowk < 20:
            return "oversold_buy"
        else:
            return "neutral"
    
    elif indicator == "ADX":
        adx = latest.get("value", 0)
        if adx > 25:
            return "strong_trend"
        else:
            return "weak_trend"
    
    return "neutral"


@_rate_limit
def get_historical_prices(symbol: str, period: str = "1year") -> dict:
    """
    Get historical daily price data for backtesting and analysis.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        period: Time period - '1month', '3months', '6months', '1year', '5years'
    
    Returns:
        dict: Historical price data including:
            - symbol: Stock ticker
            - period: Requested period
            - prices: List of daily OHLCV data
            - returns: List of daily returns
            - statistics: Summary statistics (mean return, volatility, etc.)
    
    Example:
        >>> get_historical_prices("AAPL", "1year")
        {'symbol': 'AAPL', 'prices': [...], 'statistics': {'volatility': 0.25, ...}}
    """
    data = _make_alpha_vantage_request({
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "full"
    })
    
    if "error" in data:
        return data
    
    time_series = data.get("Time Series (Daily)", {})
    
    if not time_series:
        return {"error": f"No historical data found for symbol: {symbol}"}
    
    # Calculate date range based on period
    period_days = {
        "1month": 30,
        "3months": 90,
        "6months": 180,
        "1year": 365,
        "5years": 1825
    }
    
    days = period_days.get(period, 365)
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Filter and process data
    prices = []
    for date_str, ohlcv in sorted(time_series.items(), reverse=True):
        date = datetime.strptime(date_str, "%Y-%m-%d")
        if date < cutoff_date:
            break
        
        prices.append({
            "date": date_str,
            "open": float(ohlcv.get("1. open", 0)),
            "high": float(ohlcv.get("2. high", 0)),
            "low": float(ohlcv.get("3. low", 0)),
            "close": float(ohlcv.get("4. close", 0)),
            "volume": int(ohlcv.get("5. volume", 0))
        })
    
    # Calculate returns
    returns = []
    for i in range(len(prices) - 1):
        current_close = prices[i]["close"]
        previous_close = prices[i + 1]["close"]
        if previous_close > 0:
            daily_return = (current_close - previous_close) / previous_close
            returns.append({
                "date": prices[i]["date"],
                "return": daily_return
            })
    
    # Calculate statistics
    if returns:
        return_values = [r["return"] for r in returns]
        import statistics
        mean_return = statistics.mean(return_values)
        volatility = statistics.stdev(return_values) if len(return_values) > 1 else 0
        
        # Annualize
        annualized_return = mean_return * 252
        annualized_volatility = volatility * (252 ** 0.5)
    else:
        mean_return = 0
        volatility = 0
        annualized_return = 0
        annualized_volatility = 0
    
    return {
        "symbol": symbol,
        "period": period,
        "data_points": len(prices),
        "prices": prices[:30],  # Return last 30 for display
        "all_prices": prices,  # Full data for calculations
        "returns": returns[:30],
        "all_returns": returns,
        "statistics": {
            "mean_daily_return": round(mean_return, 6),
            "daily_volatility": round(volatility, 6),
            "annualized_return": round(annualized_return, 4),
            "annualized_volatility": round(annualized_volatility, 4),
            "start_price": prices[-1]["close"] if prices else 0,
            "end_price": prices[0]["close"] if prices else 0,
            "total_return": round((prices[0]["close"] - prices[-1]["close"]) / prices[-1]["close"], 4) if prices and prices[-1]["close"] > 0 else 0
        }
    }


def get_sector_performance() -> dict:
    """
    Get performance data for all market sectors.
    
    Returns:
        dict: Sector performance data including:
            - sectors: List of sector performance metrics
            - market_sentiment: Overall market direction
            - top_sectors: Best performing sectors
            - bottom_sectors: Worst performing sectors
    
    Example:
        >>> get_sector_performance()
        {'sectors': [...], 'top_sectors': ['Technology', 'Healthcare'], ...}
    """
    # Sector ETF symbols that represent each sector
    sector_etfs = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP",
        "Energy": "XLE",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Communication Services": "XLC"
    }
    
    sectors = []
    
    # Note: This will make multiple API calls, so we'll use cached data
    # or a simplified approach for the free tier
    for sector_name, etf_symbol in sector_etfs.items():
        # Get quote data for each sector ETF
        quote = get_stock_quote(etf_symbol)
        
        if "error" not in quote:
            sectors.append({
                "sector": sector_name,
                "etf_symbol": etf_symbol,
                "price": quote.get("price", 0),
                "change_percent": _safe_float(str(quote.get("change_percent", "0")).replace("%", "")),
                "volume": quote.get("volume", 0)
            })
        
        # Add small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Sort by performance
    sectors.sort(key=lambda x: x.get("change_percent", 0), reverse=True)
    
    # Determine market sentiment
    avg_change = sum(s.get("change_percent", 0) for s in sectors) / len(sectors) if sectors else 0
    
    if avg_change > 0.5:
        sentiment = "bullish"
    elif avg_change < -0.5:
        sentiment = "bearish"
    else:
        sentiment = "neutral"
    
    return {
        "sectors": sectors,
        "market_sentiment": sentiment,
        "average_change": round(avg_change, 2),
        "top_sectors": [s["sector"] for s in sectors[:3]],
        "bottom_sectors": [s["sector"] for s in sectors[-3:]],
        "timestamp": datetime.now().isoformat()
    }


@_rate_limit
def search_stocks(keywords: str) -> dict:
    """
    Search for stocks by company name or keywords.
    
    Args:
        keywords: Search keywords (company name, ticker, etc.)
    
    Returns:
        dict: Search results including:
            - results: List of matching stocks
            - count: Number of matches
    
    Example:
        >>> search_stocks("Apple")
        {'results': [{'symbol': 'AAPL', 'name': 'Apple Inc', ...}], 'count': 5}
    """
    data = _make_alpha_vantage_request({
        "function": "SYMBOL_SEARCH",
        "keywords": keywords
    })
    
    if "error" in data:
        return data
    
    matches = data.get("bestMatches", [])
    
    results = []
    for match in matches:
        score = _safe_float(match.get("9. matchScore"))
        if score < 0.3:  # Skip low-quality matches
            continue
        results.append({
            "symbol": match.get("1. symbol", ""),
            "name": match.get("2. name", ""),
            "type": match.get("3. type", ""),
            "region": match.get("4. region", ""),
            "currency": match.get("8. currency", ""),
            "match_score": score
        })

    return {
        "query": keywords,
        "results": results,
        "count": len(results)
    }


# Batch operation to get multiple stock quotes efficiently
def get_multiple_quotes(symbols: list[str]) -> dict:
    """
    Get quotes for multiple symbols with rate limiting.
    
    Args:
        symbols: List of stock ticker symbols
    
    Returns:
        dict: Quotes for all requested symbols
    """
    quotes = {}
    errors = []
    
    for symbol in symbols:
        quote = get_stock_quote(symbol)
        if "error" in quote:
            errors.append({"symbol": symbol, "error": quote["error"]})
        else:
            quotes[symbol] = quote
    
    return {
        "quotes": quotes,
        "errors": errors,
        "success_count": len(quotes),
        "error_count": len(errors)
    }
