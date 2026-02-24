"""
Macroeconomic Data Tools

This module provides functions to fetch and analyze macroeconomic indicators
using Alpha Vantage's economic data endpoints.

Indicators tracked:
- Real GDP and GDP growth
- Inflation rate (CPI)
- Unemployment rate
- Federal Funds Rate (interest rates)
- Consumer sentiment
"""

import os
from datetime import datetime
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


def _make_request(params: dict) -> dict:
    """Make a request to Alpha Vantage API."""
    params["apikey"] = ALPHA_VANTAGE_API_KEY
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(ALPHA_VANTAGE_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "Error Message" in data:
                return {"error": data["Error Message"]}
            if "Note" in data:
                return {"error": f"Rate limit: {data['Note']}"}
            
            return data
    except Exception as e:
        return {"error": str(e)}


def get_economic_indicators() -> dict:
    """
    Fetch current macroeconomic indicators for market analysis.
    
    Returns:
        dict: Economic indicators including:
            - gdp: Real GDP growth rate
            - inflation: Current inflation rate (CPI)
            - unemployment: Unemployment rate
            - interest_rate: Federal funds rate
            - consumer_sentiment: Consumer confidence
            - market_outlook: Derived market outlook score
    
    Example:
        >>> get_economic_indicators()
        {
            'gdp_growth': 2.5,
            'inflation': 3.2,
            'unemployment': 3.8,
            'interest_rate': 5.25,
            'market_outlook': {'score': 65, 'sentiment': 'cautiously_bullish'}
        }
    """
    indicators = {}
    
    # Fetch Real GDP
    gdp_data = _make_request({"function": "REAL_GDP", "interval": "quarterly"})
    if "error" not in gdp_data and "data" in gdp_data:
        recent_gdp = gdp_data["data"][:4] if gdp_data["data"] else []
        if len(recent_gdp) >= 2:
            try:
                current = float(recent_gdp[0].get("value", 0))
                previous = float(recent_gdp[1].get("value", 0))
                gdp_growth = ((current - previous) / previous * 100) if previous else 0
                indicators["gdp"] = {
                    "current_value": current,
                    "growth_rate": round(gdp_growth, 2),
                    "date": recent_gdp[0].get("date", ""),
                    "trend": "growing" if gdp_growth > 0 else "contracting"
                }
            except (ValueError, TypeError):
                indicators["gdp"] = {"error": "Could not parse GDP data"}
    
    # Fetch Inflation (CPI)
    inflation_data = _make_request({"function": "INFLATION"})
    if "error" not in inflation_data and "data" in inflation_data:
        recent_inflation = inflation_data["data"][:1] if inflation_data["data"] else []
        if recent_inflation:
            try:
                inflation_rate = float(recent_inflation[0].get("value", 0))
                indicators["inflation"] = {
                    "rate": inflation_rate,
                    "date": recent_inflation[0].get("date", ""),
                    "assessment": _assess_inflation(inflation_rate)
                }
            except (ValueError, TypeError):
                indicators["inflation"] = {"error": "Could not parse inflation data"}
    
    # Fetch Unemployment Rate
    unemployment_data = _make_request({"function": "UNEMPLOYMENT"})
    if "error" not in unemployment_data and "data" in unemployment_data:
        recent_unemployment = unemployment_data["data"][:1] if unemployment_data["data"] else []
        if recent_unemployment:
            try:
                unemployment_rate = float(recent_unemployment[0].get("value", 0))
                indicators["unemployment"] = {
                    "rate": unemployment_rate,
                    "date": recent_unemployment[0].get("date", ""),
                    "assessment": _assess_unemployment(unemployment_rate)
                }
            except (ValueError, TypeError):
                indicators["unemployment"] = {"error": "Could not parse unemployment data"}
    
    # Fetch Federal Funds Rate
    rate_data = _make_request({"function": "FEDERAL_FUNDS_RATE", "interval": "monthly"})
    if "error" not in rate_data and "data" in rate_data:
        recent_rate = rate_data["data"][:2] if rate_data["data"] else []
        if recent_rate:
            try:
                current_rate = float(recent_rate[0].get("value", 0))
                previous_rate = float(recent_rate[1].get("value", 0)) if len(recent_rate) > 1 else current_rate
                indicators["interest_rate"] = {
                    "rate": current_rate,
                    "previous_rate": previous_rate,
                    "date": recent_rate[0].get("date", ""),
                    "trend": _assess_rate_trend(current_rate, previous_rate),
                    "policy_stance": _assess_monetary_policy(current_rate)
                }
            except (ValueError, TypeError):
                indicators["interest_rate"] = {"error": "Could not parse interest rate data"}
    
    # Fetch Consumer Sentiment
    sentiment_data = _make_request({"function": "CONSUMER_SENTIMENT"})
    if "error" not in sentiment_data and "data" in sentiment_data:
        recent_sentiment = sentiment_data["data"][:1] if sentiment_data["data"] else []
        if recent_sentiment:
            try:
                sentiment_value = float(recent_sentiment[0].get("value", 0))
                indicators["consumer_sentiment"] = {
                    "value": sentiment_value,
                    "date": recent_sentiment[0].get("date", ""),
                    "assessment": _assess_sentiment(sentiment_value)
                }
            except (ValueError, TypeError):
                indicators["consumer_sentiment"] = {"error": "Could not parse sentiment data"}
    
    # Calculate overall market outlook
    indicators["market_outlook"] = calculate_market_outlook_score(indicators)
    indicators["timestamp"] = datetime.now().isoformat()
    
    return indicators


def calculate_market_outlook_score(indicators: dict) -> dict:
    """
    Calculate an overall market outlook score based on economic indicators.
    
    The score ranges from 0 (very bearish) to 100 (very bullish).
    
    Methodology:
    - GDP growth: +10 to +25 points (positive growth)
    - Inflation: -15 to +15 points (optimal around 2%)
    - Unemployment: -10 to +20 points (lower is better)
    - Interest rates: -10 to +10 points
    - Consumer sentiment: -10 to +20 points
    
    Args:
        indicators: Dictionary of economic indicators
    
    Returns:
        dict: Market outlook including:
            - score: 0-100 score
            - sentiment: Qualitative assessment
            - factors: Breakdown of scoring factors
    
    Example:
        >>> calculate_market_outlook_score(indicators)
        {'score': 72, 'sentiment': 'moderately_bullish', 'factors': {...}}
    """
    score = 50  # Start neutral
    factors = {}
    
    # GDP Factor (max +25 or -15)
    gdp = indicators.get("gdp", {})
    if isinstance(gdp, dict) and "growth_rate" in gdp:
        growth = gdp["growth_rate"]
        if growth > 3:
            gdp_score = 25
        elif growth > 2:
            gdp_score = 20
        elif growth > 1:
            gdp_score = 15
        elif growth > 0:
            gdp_score = 10
        elif growth > -1:
            gdp_score = -5
        else:
            gdp_score = -15
        score += gdp_score
        factors["gdp"] = {"growth_rate": growth, "score_impact": gdp_score}
    
    # Inflation Factor (optimal ~2%, max +15 or -15)
    inflation = indicators.get("inflation", {})
    if isinstance(inflation, dict) and "rate" in inflation:
        rate = inflation["rate"]
        if 1.5 <= rate <= 2.5:
            inflation_score = 15  # Goldilocks zone
        elif 1 <= rate <= 3:
            inflation_score = 10
        elif rate < 1:
            inflation_score = -5  # Deflation risk
        elif rate <= 4:
            inflation_score = 0
        elif rate <= 6:
            inflation_score = -10
        else:
            inflation_score = -15  # High inflation
        score += inflation_score
        factors["inflation"] = {"rate": rate, "score_impact": inflation_score}
    
    # Unemployment Factor (max +20 or -10)
    unemployment = indicators.get("unemployment", {})
    if isinstance(unemployment, dict) and "rate" in unemployment:
        rate = unemployment["rate"]
        if rate < 4:
            unemployment_score = 20
        elif rate < 5:
            unemployment_score = 15
        elif rate < 6:
            unemployment_score = 10
        elif rate < 7:
            unemployment_score = 0
        else:
            unemployment_score = -10
        score += unemployment_score
        factors["unemployment"] = {"rate": rate, "score_impact": unemployment_score}
    
    # Interest Rate Factor (max +10 or -10)
    interest = indicators.get("interest_rate", {})
    if isinstance(interest, dict) and "rate" in interest:
        rate = interest["rate"]
        trend = interest.get("trend", "stable")
        
        # Higher rates generally negative for stocks, but context matters
        if rate < 2:
            rate_score = 10  # Accommodative
        elif rate < 4:
            rate_score = 5  # Moderate
        elif rate < 6:
            rate_score = 0  # Neutral
        else:
            rate_score = -10  # Restrictive
        
        # Adjust for trend
        if trend == "rising":
            rate_score -= 5
        elif trend == "falling":
            rate_score += 5
        
        score += rate_score
        factors["interest_rate"] = {"rate": rate, "trend": trend, "score_impact": rate_score}
    
    # Consumer Sentiment Factor (max +20 or -10)
    sentiment = indicators.get("consumer_sentiment", {})
    if isinstance(sentiment, dict) and "value" in sentiment:
        value = sentiment["value"]
        if value > 95:
            sentiment_score = 20
        elif value > 85:
            sentiment_score = 15
        elif value > 75:
            sentiment_score = 10
        elif value > 65:
            sentiment_score = 5
        elif value > 55:
            sentiment_score = 0
        else:
            sentiment_score = -10
        score += sentiment_score
        factors["consumer_sentiment"] = {"value": value, "score_impact": sentiment_score}
    
    # Clamp score to 0-100
    score = max(0, min(100, score))
    
    # Determine sentiment label
    if score >= 80:
        sentiment_label = "very_bullish"
    elif score >= 65:
        sentiment_label = "moderately_bullish"
    elif score >= 50:
        sentiment_label = "cautiously_bullish"
    elif score >= 40:
        sentiment_label = "neutral"
    elif score >= 25:
        sentiment_label = "cautiously_bearish"
    else:
        sentiment_label = "bearish"
    
    return {
        "score": score,
        "sentiment": sentiment_label,
        "factors": factors,
        "recommendation": _get_outlook_recommendation(sentiment_label)
    }


def _assess_inflation(rate: float) -> str:
    """Assess inflation level."""
    if rate < 1:
        return "deflation_risk"
    elif rate < 2:
        return "below_target"
    elif rate <= 3:
        return "on_target"
    elif rate <= 5:
        return "elevated"
    else:
        return "high"


def _assess_unemployment(rate: float) -> str:
    """Assess unemployment level."""
    if rate < 4:
        return "full_employment"
    elif rate < 5:
        return "healthy"
    elif rate < 6:
        return "moderate"
    elif rate < 8:
        return "concerning"
    else:
        return "high"


def _assess_rate_trend(current: float, previous: float) -> str:
    """Assess interest rate trend."""
    diff = current - previous
    if diff > 0.25:
        return "rising"
    elif diff < -0.25:
        return "falling"
    else:
        return "stable"


def _assess_monetary_policy(rate: float) -> str:
    """Assess monetary policy stance based on rates."""
    if rate < 1:
        return "very_accommodative"
    elif rate < 2.5:
        return "accommodative"
    elif rate < 4:
        return "neutral"
    elif rate < 5.5:
        return "restrictive"
    else:
        return "very_restrictive"


def _assess_sentiment(value: float) -> str:
    """Assess consumer sentiment."""
    if value > 100:
        return "very_optimistic"
    elif value > 85:
        return "optimistic"
    elif value > 70:
        return "neutral"
    elif value > 55:
        return "pessimistic"
    else:
        return "very_pessimistic"


def _get_outlook_recommendation(sentiment: str) -> str:
    """Get investment recommendation based on outlook."""
    recommendations = {
        "very_bullish": "Consider growth-oriented sectors like Technology and Consumer Discretionary. Market conditions favor risk-on assets.",
        "moderately_bullish": "Balanced approach recommended. Mix of growth and value stocks. Consider diversified sector exposure.",
        "cautiously_bullish": "Lean towards quality stocks with strong fundamentals. Consider some defensive positions.",
        "neutral": "Focus on diversification and quality. Balance between growth and defensive sectors.",
        "cautiously_bearish": "Increase allocation to defensive sectors (Utilities, Healthcare, Consumer Staples). Consider dividend stocks.",
        "bearish": "Defensive positioning recommended. Focus on stable dividend payers, utilities, and cash positions."
    }
    return recommendations.get(sentiment, "Maintain diversified portfolio across sectors.")


def get_recession_indicators() -> dict:
    """
    Calculate recession probability based on economic indicators.
    
    Uses multiple signals:
    - Yield curve (if available)
    - GDP trend
    - Unemployment trend
    - Leading indicators
    
    Returns:
        dict: Recession analysis including probability and signals
    """
    indicators = get_economic_indicators()
    
    recession_signals = []
    probability = 0
    
    # GDP signal
    gdp = indicators.get("gdp", {})
    if isinstance(gdp, dict) and "growth_rate" in gdp:
        growth = gdp["growth_rate"]
        if growth < 0:
            recession_signals.append("negative_gdp_growth")
            probability += 30
        elif growth < 1:
            recession_signals.append("slowing_gdp")
            probability += 15
    
    # Unemployment signal
    unemployment = indicators.get("unemployment", {})
    if isinstance(unemployment, dict) and "rate" in unemployment:
        rate = unemployment["rate"]
        if rate > 6:
            recession_signals.append("high_unemployment")
            probability += 25
        elif rate > 5:
            recession_signals.append("rising_unemployment")
            probability += 10
    
    # Interest rate signal (inverted yield curve proxy)
    interest = indicators.get("interest_rate", {})
    if isinstance(interest, dict) and "policy_stance" in interest:
        stance = interest["policy_stance"]
        if stance == "very_restrictive":
            recession_signals.append("tight_monetary_policy")
            probability += 20
        elif stance == "restrictive":
            recession_signals.append("moderately_tight_policy")
            probability += 10
    
    # Consumer sentiment signal
    sentiment = indicators.get("consumer_sentiment", {})
    if isinstance(sentiment, dict) and "value" in sentiment:
        value = sentiment["value"]
        if value < 55:
            recession_signals.append("weak_consumer_confidence")
            probability += 15
        elif value < 70:
            recession_signals.append("declining_confidence")
            probability += 5
    
    probability = min(probability, 100)
    
    if probability >= 70:
        risk_level = "high"
    elif probability >= 40:
        risk_level = "moderate"
    else:
        risk_level = "low"
    
    return {
        "recession_probability": probability,
        "risk_level": risk_level,
        "signals": recession_signals,
        "signal_count": len(recession_signals),
        "recommendation": _get_recession_recommendation(risk_level)
    }


def _get_recession_recommendation(risk_level: str) -> str:
    """Get recommendation based on recession risk."""
    recommendations = {
        "high": "Consider defensive positioning. Increase allocations to bonds, utilities, and consumer staples. Maintain cash reserves.",
        "moderate": "Balanced approach with emphasis on quality. Focus on companies with strong balance sheets and stable cash flows.",
        "low": "Favorable conditions for equity allocation. Consider growth sectors while maintaining diversification."
    }
    return recommendations.get(risk_level, "Maintain diversified portfolio.")
