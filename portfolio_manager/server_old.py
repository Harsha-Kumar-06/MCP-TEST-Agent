"""
Portfolio Manager - FastAPI Server

This module provides the REST API and web interface for the portfolio manager.
It integrates Google ADK with FastAPI for serving the multi-agent system.

Usage:
    uvicorn portfolio_manager.server:app --reload --port 8001
    
    Or use ADK web UI:
    adk web portfolio_manager/
"""

# Python 3.9 compatibility patch for Google ADK
# ADK assumes Python 3.10+ and uses types.UnionType which doesn't exist in 3.9
import sys
import types

if sys.version_info < (3, 10):
    # Add a dummy UnionType for Python 3.9 compatibility
    # This prevents AttributeError when ADK tries to check for UnionType
    if not hasattr(types, 'UnionType'):
        types.UnionType = type(None)  # Use a dummy type that won't match real unions

import os
import json
import uuid
import asyncio
from typing import Optional, Dict, List, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from dotenv import load_dotenv

# Load environment variables from the correct path BEFORE importing agents
# This ensures GOOGLE_API_KEY is available when Google ADK initializes
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path)

# Verify API key is loaded
if not os.environ.get("GOOGLE_API_KEY"):
    print("WARNING: GOOGLE_API_KEY not found in environment variables!")

# Google ADK imports for agent integration (reads GOOGLE_API_KEY from env automatically)
from google.adk.runners import InMemoryRunner
from google.genai import types

# Import the portfolio agent
from portfolio_manager.agent import root_agent

# FastAPI app configuration
app = FastAPI(
    title="Automated Portfolio Manager",
    description="""
    AI-powered investment portfolio manager that creates personalized,
    data-driven investment portfolios based on your risk profile and market conditions.
    
    ## Features
    - Interactive risk assessment questionnaire
    - Macroeconomic analysis
    - Sector selection based on market conditions
    - Stock selection using fundamental and technical analysis
    - Portfolio construction with proper diversification
    - Historical backtesting validation
    - Comprehensive investment reports
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web UI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# Request/Response Models
class PortfolioRequest(BaseModel):
    """Request model for portfolio generation."""
    capital: float = Field(..., description="Investment capital")
    goal: str = Field(default="balanced_growth", description="Investment goal")
    horizon: str = Field(default="3_5_years", description="Time horizon")
    max_loss: int = Field(default=15, description="Maximum acceptable loss percentage")
    experience: str = Field(default="intermediate", description="Investment experience")
    income_stability: str = Field(default="stable", description="Income stability")


class PortfolioResponse(BaseModel):
    """Response model for portfolio generation."""
    success: bool
    profile: Dict[str, Any]
    market_analysis: Dict[str, Any]
    sectors: Dict[str, Any]
    holdings: List[Dict[str, Any]]
    performance: Dict[str, Any]
    summary: Dict[str, Any]
    ai_analysis: Optional[str] = None  # AI agent generated analysis


def load_cached_fundamentals() -> Dict[str, Any]:
    """Load cached stock fundamentals data."""
    try:
        with open(os.path.join(DATA_DIR, "cached_fundamentals.json"), "r") as f:
            return json.load(f)
    except Exception:
        return {"stocks": {}}


def calculate_risk_score(goal: str, max_loss: int, experience: str) -> int:
    """Calculate risk score from 1-10 based on profile."""
    goal_scores = {
        "preserve_capital": 2,
        "income": 4,
        "balanced_growth": 6,
        "aggressive_growth": 8
    }
    exp_bonus = {"beginner": -1, "intermediate": 0, "advanced": 1, "expert": 2}
    
    base = goal_scores.get(goal, 5)
    loss_factor = min(max_loss / 10, 2)  # Cap at +2
    exp_factor = exp_bonus.get(experience, 0)
    
    return max(1, min(10, int(base + loss_factor + exp_factor)))


def select_sectors_for_profile(risk_score: int, goal: str) -> Dict[str, Any]:
    """Select optimal sectors based on risk profile."""
    # Defensive sectors for lower risk
    defensive = [
        {"name": "Utilities", "weight": 30, "type": "defensive"},
        {"name": "Consumer Staples", "weight": 30, "type": "defensive"},
        {"name": "Healthcare", "weight": 25, "type": "defensive"},
    ]
    
    # Growth sectors for higher risk
    growth = [
        {"name": "Technology", "weight": 35, "type": "growth"},
        {"name": "Financials", "weight": 25, "type": "growth"},
        {"name": "Healthcare", "weight": 20, "type": "growth"},
    ]
    
    # Balanced mix
    balanced = [
        {"name": "Healthcare", "weight": 25, "type": "defensive"},
        {"name": "Consumer Staples", "weight": 20, "type": "defensive"},
        {"name": "Technology", "weight": 20, "type": "growth"},
        {"name": "Financials", "weight": 20, "type": "growth"},
        {"name": "Utilities", "weight": 15, "type": "defensive"},
    ]
    
    # Income-focused
    income_sectors = [
        {"name": "Utilities", "weight": 35, "type": "income"},
        {"name": "Consumer Staples", "weight": 25, "type": "income"},
        {"name": "Healthcare", "weight": 20, "type": "defensive"},
        {"name": "Energy", "weight": 20, "type": "income"},
    ]
    
    if goal == "income":
        sectors = income_sectors
    elif risk_score <= 3:
        sectors = defensive
    elif risk_score >= 7:
        sectors = growth
    else:
        sectors = balanced
    
    return {
        "selected": sectors,
        "rationale": f"Sectors selected based on risk score {risk_score}/10 and {goal} objective",
        "defensive_pct": sum(s["weight"] for s in sectors if s["type"] in ["defensive", "income"]),
        "growth_pct": sum(s["weight"] for s in sectors if s["type"] == "growth")
    }


def select_stocks_for_sectors(sectors: List[Dict], capital: float, risk_score: int) -> List[Dict[str, Any]]:
    """Select stocks for each sector from cached fundamentals."""
    fundamentals = load_cached_fundamentals()
    stocks_data = fundamentals.get("stocks", {})
    
    # Map sectors to stocks
    sector_stocks = {
        "Utilities": ["NEE", "DUK", "SO", "D"],
        "Consumer Staples": ["PG", "KO", "PEP", "COST", "WMT"],
        "Healthcare": ["UNH", "JNJ", "PFE", "ABBV", "MRK"],
        "Technology": ["AAPL", "MSFT"],
        "Energy": ["XOM", "CVX"],
        "Financials": ["JPM", "V"]
    }
    
    holdings = []
    invested_capital = capital * 0.95  # 5% cash reserve
    
    for sector in sectors:
        sector_name = sector["name"]
        sector_weight = sector["weight"] / 100
        sector_capital = invested_capital * sector_weight
        
        available_stocks = sector_stocks.get(sector_name, [])
        # Pick 1-2 stocks per sector
        num_stocks = 2 if sector_weight >= 0.25 else 1
        
        for i, symbol in enumerate(available_stocks[:num_stocks]):
            stock_data = stocks_data.get(symbol, {})
            if not stock_data:
                continue
            
            stock_capital = sector_capital / num_stocks
            price = stock_data.get("price", 100)
            shares = int(stock_capital / price)
            
            if shares > 0:
                holdings.append({
                    "symbol": symbol,
                    "name": stock_data.get("name", symbol),
                    "sector": sector_name,
                    "shares": shares,
                    "price": price,
                    "value": round(shares * price, 2),
                    "weight": round((shares * price / invested_capital) * 100, 1),
                    "metrics": {
                        "pe_ratio": stock_data.get("pe_ratio", 0),
                        "dividend_yield": stock_data.get("dividend_yield", 0),
                        "beta": stock_data.get("beta", 1),
                        "profit_margin": stock_data.get("profit_margin", 0)
                    }
                })
    
    return holdings


def calculate_portfolio_performance(holdings: List[Dict], risk_score: int) -> Dict[str, Any]:
    """Calculate expected portfolio performance metrics."""
    if not holdings:
        return {
            "expected_return": 0,
            "volatility": 0,
            "sharpe_ratio": 0,
            "dividend_yield": 0,
            "beta": 0
        }
    
    total_value = sum(h["value"] for h in holdings)
    
    # Weighted averages
    weighted_beta = sum(h["value"] * h["metrics"]["beta"] for h in holdings) / total_value
    weighted_div = sum(h["value"] * h["metrics"]["dividend_yield"] for h in holdings) / total_value
    
    # Estimate returns based on composition and historical averages
    base_return = 0.08  # 8% base market return
    risk_adjustment = (risk_score - 5) * 0.01  # +/- 1% per risk level from 5
    
    expected_return = base_return + risk_adjustment + (weighted_div / 100)
    volatility = 0.10 + (weighted_beta - 1) * 0.05  # Base 10% + beta adjustment
    sharpe = (expected_return - 0.04) / volatility if volatility > 0 else 0  # RF = 4%
    
    return {
        "expected_return": round(expected_return * 100, 1),
        "volatility": round(volatility * 100, 1),
        "sharpe_ratio": round(sharpe, 2),
        "dividend_yield": round(weighted_div, 2),
        "beta": round(weighted_beta, 2),
        "var_95": round(total_value * volatility * 1.65, 2),  # 95% VaR
        "max_drawdown": round(volatility * 2 * 100, 1)  # Estimated
    }


async def run_portfolio_agent(capital: float, goal: str, horizon: str, max_loss: int, experience: str, income_stability: str) -> Dict[str, Any]:
    """
    Run the AI agent pipeline to generate a portfolio.
    
    This uses the ADK InMemoryRunner to execute the root_agent which orchestrates:
    - Macro analysis
    - Sector selection
    - Stock selection
    - Portfolio construction
    - Performance analysis
    - Report generation
    """
    # Create a fresh runner for each request
    runner = InMemoryRunner(agent=root_agent, app_name="portfolio_manager")
    
    # Create a new session
    session = await runner.session_service.create_session(
        app_name="portfolio_manager",
        user_id="web_user"
    )
    
    # Construct the complete profile message to skip conversational collection
    profile_message = f"""I want to generate a portfolio with the following profile already collected:

Investment Capital: ${capital:,.2f}
Investment Goal: {goal.replace('_', ' ')}
Time Horizon: {horizon.replace('_', ' ')}
Maximum Acceptable Loss: {max_loss}%
Investment Experience: {experience}
Income Stability: {income_stability}

Please skip the profile collection phase and proceed directly to generate my personalized portfolio using the analysis pipeline. Run through all the sub-agents (macro analysis, sector selection, stock selection, portfolio construction, performance analysis, backtesting, and report generation) and provide me with the complete portfolio report."""

    # Send message to agent
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=profile_message)]
    )
    
    # Collect agent responses
    collected_output = []
    
    async for event in runner.run_async(
        user_id="web_user",
        session_id=session.id,
        new_message=message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text and part.text.strip():
                    collected_output.append(part.text.strip())
    
    # Combine all responses
    full_response = "\n\n".join(collected_output)
    
    return {
        "agent_response": full_response,
        "session_id": session.id
    }


@app.post("/api/generate-portfolio", response_model=PortfolioResponse)
async def generate_portfolio(request: PortfolioRequest):
    """
    Generate a portfolio based on user profile using AI agents.
    
    This endpoint:
    1. Runs the AI agent pipeline for comprehensive analysis
    2. Also generates structured data for charts/tables
    """
    try:
        # Run AI agent pipeline
        agent_result = await run_portfolio_agent(
            capital=request.capital,
            goal=request.goal,
            horizon=request.horizon,
            max_loss=request.max_loss,
            experience=request.experience,
            income_stability=request.income_stability
        )
        ai_analysis = agent_result.get("agent_response", "")
        
        # Also generate structured data for UI visualization
        risk_score = calculate_risk_score(request.goal, request.max_loss, request.experience)
        
        # Build profile
        profile = {
            "capital": request.capital,
            "goal": request.goal.replace("_", " ").title(),
            "horizon": request.horizon.replace("_", " "),
            "max_loss": request.max_loss,
            "experience": request.experience.title(),
            "risk_score": risk_score,
            "risk_label": ["Ultra Conservative", "Very Conservative", "Conservative", 
                          "Moderately Conservative", "Moderate", "Moderately Aggressive",
                          "Growth", "Aggressive", "Very Aggressive", "Maximum Risk"][risk_score - 1]
        }
        
        # Market analysis (simulated current conditions)
        market_analysis = {
            "sentiment": "neutral",
            "confidence": 65,
            "conditions": {
                "gdp": "moderate growth",
                "inflation": "elevated",
                "rates": "restrictive",
                "employment": "healthy"
            },
            "outlook": "Moderate growth with elevated inflation suggests a balanced approach favoring quality and income.",
            "favored_sectors": ["Utilities", "Consumer Staples", "Healthcare"],
            "sectors_to_avoid": ["High-growth Tech", "Speculative"]
        }
        
        # Select sectors
        sector_data = select_sectors_for_profile(risk_score, request.goal)
        
        # Select stocks
        holdings = select_stocks_for_sectors(sector_data["selected"], request.capital, risk_score)
        
        # Calculate performance
        performance = calculate_portfolio_performance(holdings, risk_score)
        
        # Summary
        total_invested = sum(h["value"] for h in holdings)
        cash_reserve = request.capital - total_invested
        
        summary = {
            "total_capital": request.capital,
            "invested": round(total_invested, 2),
            "cash_reserve": round(cash_reserve, 2),
            "cash_pct": round((cash_reserve / request.capital) * 100, 1),
            "num_positions": len(holdings),
            "num_sectors": len(set(h["sector"] for h in holdings)),
            "generated_at": "2026-02-20"
        }
        
        return PortfolioResponse(
            success=True,
            profile=profile,
            market_analysis=market_analysis,
            sectors=sector_data,
            holdings=holdings,
            performance=performance,
            summary=summary,
            ai_analysis=ai_analysis
        )
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error generating portfolio: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page with advanced stock management UI."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Portfolio Manager | AI-Powered Investment</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            :root {
                --primary: #1a73e8;
                --primary-dark: #1557b0;
                --success: #34a853;
                --warning: #fbbc04;
                --danger: #ea4335;
                --bg-dark: #1e222d;
                --bg-card: #252932;
                --bg-input: #2a2e39;
                --text-primary: #e8eaed;
                --text-secondary: #9aa0a6;
                --border: #3c4043;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg-dark);
                color: var(--text-primary);
                min-height: 100vh;
            }
            
            /* Header */
            .header {
                background: var(--bg-card);
                padding: 16px 32px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--border);
            }
            
            .logo {
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 20px;
                font-weight: 600;
            }
            
            .logo-icon {
                width: 36px;
                height: 36px;
                background: linear-gradient(135deg, var(--primary), var(--success));
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            }
            
            .header-actions {
                display: flex;
                gap: 16px;
                align-items: center;
            }
            
            .status-badge {
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                background: rgba(52, 168, 83, 0.15);
                color: var(--success);
            }
            
            /* Main Layout */
            .main-container {
                display: grid;
                grid-template-columns: 380px 1fr;
                height: calc(100vh - 69px);
            }
            
            /* Left Panel - Profile Form */
            .profile-panel {
                background: var(--bg-card);
                border-right: 1px solid var(--border);
                overflow-y: auto;
                padding: 24px;
            }
            
            .panel-title {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .form-section {
                margin-bottom: 20px;
            }
            
            .form-label {
                display: block;
                font-size: 13px;
                color: var(--text-secondary);
                margin-bottom: 8px;
                font-weight: 500;
            }
            
            .form-input, .form-select {
                width: 100%;
                padding: 12px 14px;
                background: var(--bg-input);
                border: 1px solid var(--border);
                border-radius: 8px;
                color: var(--text-primary);
                font-size: 14px;
                transition: border-color 0.2s, box-shadow 0.2s;
            }
            
            .form-input:focus, .form-select:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.2);
            }
            
            .form-select {
                cursor: pointer;
                appearance: none;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%239aa0a6' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10l-5 5z'/%3E%3C/svg%3E");
                background-repeat: no-repeat;
                background-position: right 12px center;
            }
            
            .form-select option {
                background: var(--bg-card);
                color: var(--text-primary);
            }
            
            .input-prefix {
                position: relative;
            }
            
            .input-prefix .form-input {
                padding-left: 32px;
            }
            
            .input-prefix::before {
                content: '$';
                position: absolute;
                left: 14px;
                top: 50%;
                transform: translateY(-50%);
                color: var(--text-secondary);
                font-size: 14px;
            }
            
            .btn {
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                border: none;
                transition: all 0.2s;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            .btn-primary {
                background: var(--primary);
                color: white;
                width: 100%;
            }
            
            .btn-primary:hover:not(:disabled) {
                background: var(--primary-dark);
            }
            
            .btn-primary:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            
            .btn-secondary {
                background: transparent;
                color: var(--text-secondary);
                border: 1px solid var(--border);
            }
            
            .btn-secondary:hover {
                background: var(--bg-input);
                color: var(--text-primary);
            }
            
            /* Right Panel - Results */
            .results-panel {
                padding: 24px;
                overflow-y: auto;
            }
            
            /* Tabs */
            .tabs {
                display: flex;
                gap: 8px;
                margin-bottom: 24px;
                border-bottom: 1px solid var(--border);
                padding-bottom: 12px;
            }
            
            .tab {
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                cursor: pointer;
                color: var(--text-secondary);
                transition: all 0.2s;
            }
            
            .tab:hover { color: var(--text-primary); }
            
            .tab.active {
                background: var(--primary);
                color: white;
            }
            
            /* Cards */
            .card {
                background: var(--bg-card);
                border-radius: 12px;
                border: 1px solid var(--border);
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
            }
            
            .card-title {
                font-size: 15px;
                font-weight: 600;
            }
            
            /* Stats Grid */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .stat-card {
                background: var(--bg-card);
                border-radius: 12px;
                border: 1px solid var(--border);
                padding: 16px;
            }
            
            .stat-label {
                font-size: 12px;
                color: var(--text-secondary);
                margin-bottom: 8px;
            }
            
            .stat-value {
                font-size: 24px;
                font-weight: 700;
            }
            
            .stat-change {
                font-size: 12px;
                margin-top: 4px;
            }
            
            .stat-change.positive { color: var(--success); }
            .stat-change.negative { color: var(--danger); }
            
            /* Table */
            .table-container {
                overflow-x: auto;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
            }
            
            th, td {
                padding: 12px 16px;
                text-align: left;
                border-bottom: 1px solid var(--border);
            }
            
            th {
                font-size: 12px;
                font-weight: 600;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            td {
                font-size: 14px;
            }
            
            tr:hover {
                background: rgba(255, 255, 255, 0.02);
            }
            
            .stock-cell {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .stock-icon {
                width: 32px;
                height: 32px;
                border-radius: 8px;
                background: var(--bg-input);
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 11px;
            }
            
            .stock-name {
                font-weight: 500;
            }
            
            .stock-symbol {
                font-size: 12px;
                color: var(--text-secondary);
            }
            
            .weight-bar {
                height: 6px;
                background: var(--bg-input);
                border-radius: 3px;
                overflow: hidden;
                width: 80px;
            }
            
            .weight-fill {
                height: 100%;
                background: var(--primary);
                border-radius: 3px;
            }
            
            /* Charts Container */
            .charts-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .chart-wrapper {
                position: relative;
                height: 250px;
            }
            
            /* Loading State */
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(30, 34, 45, 0.95);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s;
            }
            
            .loading-overlay.active {
                opacity: 1;
                visibility: visible;
            }
            
            .loading-spinner {
                width: 60px;
                height: 60px;
                border: 3px solid var(--border);
                border-top-color: var(--primary);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .loading-text {
                margin-top: 20px;
                font-size: 16px;
                color: var(--text-secondary);
            }
            
            .loading-steps {
                margin-top: 24px;
                text-align: left;
            }
            
            .loading-step {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 8px 0;
                color: var(--text-secondary);
                font-size: 14px;
            }
            
            .loading-step.active {
                color: var(--text-primary);
            }
            
            .loading-step.done {
                color: var(--success);
            }
            
            .step-icon {
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: var(--bg-input);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
            }
            
            .loading-step.active .step-icon {
                background: var(--primary);
            }
            
            .loading-step.done .step-icon {
                background: var(--success);
            }
            
            /* Chat Mode */
            .chat-toggle {
                margin-top: 16px;
                text-align: center;
            }
            
            .chat-toggle a {
                color: var(--primary);
                text-decoration: none;
                font-size: 13px;
            }
            
            .chat-container {
                display: none;
                flex-direction: column;
                height: calc(100% - 60px);
            }
            
            .chat-container.active {
                display: flex;
            }
            
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 16px 0;
            }
            
            .chat-message {
                margin-bottom: 16px;
                display: flex;
                gap: 12px;
            }
            
            .chat-message.user {
                flex-direction: row-reverse;
            }
            
            .chat-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: var(--bg-input);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                flex-shrink: 0;
            }
            
            .chat-message.user .chat-avatar {
                background: var(--primary);
            }
            
            .chat-bubble {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 12px;
                background: var(--bg-input);
                font-size: 14px;
                line-height: 1.5;
            }
            
            .chat-message.user .chat-bubble {
                background: var(--primary);
            }
            
            .chat-input-row {
                display: flex;
                gap: 12px;
                padding-top: 16px;
                border-top: 1px solid var(--border);
            }
            
            .chat-input-row .form-input {
                flex: 1;
            }
            
            /* Empty State */
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: var(--text-secondary);
            }
            
            .empty-icon {
                font-size: 48px;
                margin-bottom: 16px;
            }
            
            .empty-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 8px;
            }
            
            /* Profile Summary */
            .profile-summary {
                background: var(--bg-input);
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 16px;
                display: none;
            }
            
            .profile-summary.active {
                display: block;
            }
            
            .profile-row {
                display: flex;
                justify-content: space-between;
                font-size: 13px;
                padding: 4px 0;
            }
            
            .profile-row-label {
                color: var(--text-secondary);
            }
            
            .risk-meter {
                display: flex;
                gap: 3px;
                margin-top: 12px;
            }
            
            .risk-bar {
                flex: 1;
                height: 6px;
                border-radius: 3px;
                background: var(--border);
            }
            
            .risk-bar.filled {
                background: var(--primary);
            }
            
            .risk-bar.filled.high {
                background: var(--danger);
            }
            
            .risk-bar.filled.medium {
                background: var(--warning);
            }
            
            .risk-bar.filled.low {
                background: var(--success);
            }
            
            /* Responsive */
            @media (max-width: 1024px) {
                .main-container {
                    grid-template-columns: 1fr;
                }
                .profile-panel {
                    border-right: none;
                    border-bottom: 1px solid var(--border);
                }
                .stats-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                .charts-row {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <!-- Header -->
        <header class="header">
            <div class="logo">
                <div class="logo-icon">📈</div>
                <span>Portfolio Manager</span>
            </div>
            <div class="header-actions">
                <span class="status-badge">● API Connected</span>
                <button class="btn btn-secondary" onclick="resetForm()">New Portfolio</button>
            </div>
        </header>
        
        <!-- Main Container -->
        <div class="main-container">
            <!-- Left Panel - Profile Form -->
            <div class="profile-panel">
                <div class="panel-title">
                    <span>📋</span> Investment Profile
                </div>
                
                <!-- Profile Summary (shown after completion) -->
                <div class="profile-summary" id="profileSummary">
                    <div class="profile-row">
                        <span class="profile-row-label">Capital</span>
                        <span id="summaryCapital">-</span>
                    </div>
                    <div class="profile-row">
                        <span class="profile-row-label">Risk Level</span>
                        <span id="summaryRisk">-</span>
                    </div>
                    <div class="risk-meter" id="riskMeter"></div>
                </div>
                
                <!-- Form Mode -->
                <form id="profileForm">
                    <div class="form-section">
                        <label class="form-label">Investment Capital *</label>
                        <div class="input-prefix">
                            <input type="number" class="form-input" id="capital" placeholder="5000" min="100" required>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <label class="form-label">Investment Goal</label>
                        <select class="form-select" id="goal">
                            <option value="">Select your goal...</option>
                            <option value="preserve_capital">Preserve Capital - Low risk</option>
                            <option value="income">Generate Income - Dividends</option>
                            <option value="balanced_growth">Balanced Growth - Moderate</option>
                            <option value="aggressive_growth">Aggressive Growth - High risk</option>
                        </select>
                    </div>
                    
                    <div class="form-section">
                        <label class="form-label">Time Horizon</label>
                        <select class="form-select" id="horizon">
                            <option value="">Select time horizon...</option>
                            <option value="<1 year">Less than 1 year</option>
                            <option value="1-3 years">1-3 years</option>
                            <option value="3-5 years">3-5 years</option>
                            <option value="5-10 years">5-10 years</option>
                            <option value="10+ years">10+ years</option>
                        </select>
                    </div>
                    
                    <div class="form-section">
                        <label class="form-label">Maximum Acceptable Loss</label>
                        <select class="form-select" id="maxLoss">
                            <option value="">Select loss tolerance...</option>
                            <option value="5">Up to 5%</option>
                            <option value="10">Up to 10%</option>
                            <option value="20">Up to 20%</option>
                            <option value="30">Up to 30%+</option>
                        </select>
                    </div>
                    
                    <div class="form-section">
                        <label class="form-label">Investment Experience</label>
                        <select class="form-select" id="experience">
                            <option value="">Select experience level...</option>
                            <option value="none">None - First time investor</option>
                            <option value="beginner">Beginner - <1 year</option>
                            <option value="intermediate">Intermediate - 1-5 years</option>
                            <option value="advanced">Advanced - 5+ years</option>
                            <option value="expert">Expert - Professional</option>
                        </select>
                    </div>
                    
                    <div class="form-section">
                        <label class="form-label">Income Stability</label>
                        <select class="form-select" id="income">
                            <option value="">Select income stability...</option>
                            <option value="very_unstable">Very Unstable</option>
                            <option value="unstable">Somewhat Unstable</option>
                            <option value="stable">Stable</option>
                            <option value="very_stable">Very Stable</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn btn-primary" id="generateBtn">
                        <span>🚀</span> Generate Portfolio
                    </button>
                </form>
                
                <div class="chat-toggle">
                    <a href="#" onclick="toggleChatMode(event)">Or use chat mode →</a>
                </div>
                
                <!-- Chat Mode -->
                <div class="chat-container" id="chatContainer">
                    <div class="chat-messages" id="chatMessages">
                        <div class="chat-message">
                            <div class="chat-avatar">🤖</div>
                            <div class="chat-bubble">
                                Hello! I'm your AI Portfolio Manager. Tell me about your investment goals and I'll create a personalized portfolio for you.
                            </div>
                        </div>
                    </div>
                    <div class="chat-input-row">
                        <input type="text" class="form-input" id="chatInput" placeholder="Type your message...">
                        <button class="btn btn-primary" onclick="sendChat()" style="width:auto;">Send</button>
                    </div>
                </div>
            </div>
            
            <!-- Right Panel - Results -->
            <div class="results-panel">
                <!-- Tabs -->
                <div class="tabs">
                    <div class="tab active" onclick="switchTab('overview')">Overview</div>
                    <div class="tab" onclick="switchTab('holdings')">Holdings</div>
                    <div class="tab" onclick="switchTab('analysis')">Analysis</div>
                </div>
                
                <!-- Empty State -->
                <div class="empty-state" id="emptyState">
                    <div class="empty-icon">📊</div>
                    <div class="empty-title">No Portfolio Generated</div>
                    <p>Complete your investment profile to generate a personalized portfolio recommendation.</p>
                </div>
                
                <!-- Overview Tab -->
                <div id="overviewTab" style="display:none;">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Total Investment</div>
                            <div class="stat-value" id="statCapital">$0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Risk Score</div>
                            <div class="stat-value" id="statRisk">-</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Positions</div>
                            <div class="stat-value" id="statPositions">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Sectors</div>
                            <div class="stat-value" id="statSectors">0</div>
                        </div>
                    </div>
                    
                    <div class="charts-row">
                        <div class="card">
                            <div class="card-header">
                                <div class="card-title">Sector Allocation</div>
                            </div>
                            <div class="chart-wrapper">
                                <canvas id="sectorChart"></canvas>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">
                                <div class="card-title">Portfolio Composition</div>
                            </div>
                            <div class="chart-wrapper">
                                <canvas id="compositionChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Holdings Tab -->
                <div id="holdingsTab" style="display:none;">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">Portfolio Holdings</div>
                        </div>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Stock</th>
                                        <th>Sector</th>
                                        <th>Shares</th>
                                        <th>Price</th>
                                        <th>Value</th>
                                        <th>Weight</th>
                                    </tr>
                                </thead>
                                <tbody id="holdingsTable">
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <!-- Analysis Tab -->
                <div id="analysisTab" style="display:none;">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">Market Analysis</div>
                        </div>
                        <div id="analysisContent" style="font-size:14px;line-height:1.7;white-space:pre-wrap;"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Loading Overlay -->
        <div class="loading-overlay" id="loadingOverlay">
            <div class="loading-spinner"></div>
            <div class="loading-text">Generating your portfolio...</div>
            <div class="loading-steps">
                <div class="loading-step" id="step1">
                    <div class="step-icon">1</div>
                    <span>Analyzing market conditions</span>
                </div>
                <div class="loading-step" id="step2">
                    <div class="step-icon">2</div>
                    <span>Selecting optimal sectors</span>
                </div>
                <div class="loading-step" id="step3">
                    <div class="step-icon">3</div>
                    <span>Evaluating stocks</span>
                </div>
                <div class="loading-step" id="step4">
                    <div class="step-icon">4</div>
                    <span>Constructing portfolio</span>
                </div>
                <div class="loading-step" id="step5">
                    <div class="step-icon">5</div>
                    <span>Generating report</span>
                </div>
            </div>
        </div>
        
        <script>
            // State
            let portfolioData = null;
            let sectorChart = null;
            let compositionChart = null;
            
            // Form submission
            document.getElementById('profileForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                await generatePortfolio();
            });
            
            // Generate portfolio using the direct API
            async function generatePortfolio() {
                const capital = parseFloat(document.getElementById('capital').value);
                const goal = document.getElementById('goal').value;
                const horizon = document.getElementById('horizon').value;
                const maxLoss = parseInt(document.getElementById('maxLoss').value) || 15;
                const experience = document.getElementById('experience').value;
                const income = document.getElementById('income').value;
                
                if (!capital || capital <= 0) {
                    alert('Please enter a valid investment capital amount');
                    return;
                }
                
                showLoading();
                
                try {
                    const response = await fetch('/api/generate-portfolio', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            capital: capital,
                            goal: goal || 'balanced_growth',
                            horizon: horizon || '3_5_years',
                            max_loss: maxLoss,
                            experience: experience || 'intermediate',
                            income_stability: income || 'stable'
                        })
                    });
                    
                    if (!response.ok) {
                        const err = await response.json();
                        throw new Error(err.detail || 'Failed to generate portfolio');
                    }
                    
                    const data = await response.json();
                    console.log('Portfolio generated:', data);
                    
                    if (data.success) {
                        portfolioData = data;
                        displayPortfolio(data);
                    } else {
                        throw new Error('Portfolio generation failed');
                    }
                    
                } catch (error) {
                    console.error('Error:', error);
                    alert('Error generating portfolio: ' + error.message);
                } finally {
                    hideLoading();
                }
            }
            
            // Display the portfolio data in the UI
            function displayPortfolio(data) {
                const { profile, market_analysis, sectors, holdings, performance, summary, ai_analysis } = data;
                
                // Update profile summary card
                document.getElementById('summaryCapital').textContent = '$' + summary.total_capital.toLocaleString();
                document.getElementById('summaryRisk').textContent = profile.risk_label;
                document.getElementById('profileSummary').classList.add('active');
                
                // Update stats
                document.getElementById('statCapital').textContent = '$' + summary.total_capital.toLocaleString();
                document.getElementById('statPositions').textContent = summary.num_positions;
                document.getElementById('statSectors').textContent = summary.num_sectors;
                document.getElementById('statRisk').textContent = profile.risk_score + '/10';
                
                // Risk meter visualization
                const riskMeter = document.getElementById('riskMeter');
                riskMeter.innerHTML = '';
                for (let i = 1; i <= 10; i++) {
                    const bar = document.createElement('div');
                    bar.className = 'risk-bar';
                    if (i <= profile.risk_score) {
                        bar.classList.add('filled');
                        if (profile.risk_score <= 3) bar.classList.add('low');
                        else if (profile.risk_score <= 6) bar.classList.add('medium');
                        else bar.classList.add('high');
                    }
                    riskMeter.appendChild(bar);
                }
                
                // Holdings table
                const tbody = document.getElementById('holdingsTable');
                tbody.innerHTML = holdings.map(h => `
                    <tr>
                        <td>
                            <div class="stock-cell">
                                <div class="stock-icon">${h.symbol.slice(0, 2)}</div>
                                <div>
                                    <div class="stock-name">${h.symbol}</div>
                                    <div class="stock-symbol">${h.name}</div>
                                </div>
                            </div>
                        </td>
                        <td><span class="sector-badge">${h.sector}</span></td>
                        <td>${h.shares}</td>
                        <td>$${h.price.toFixed(2)}</td>
                        <td>$${h.value.toLocaleString()}</td>
                        <td>
                            <div style="display:flex;align-items:center;gap:8px;">
                                <div class="weight-bar"><div class="weight-fill" style="width:${h.weight}%"></div></div>
                                <span>${h.weight}%</span>
                            </div>
                        </td>
                    </tr>
                `).join('');
                
                // Analysis content - formatted nicely
                const analysisHtml = `
                    <div style="font-family: inherit; line-height: 1.8;">
                        <div style="margin-bottom: 24px;">
                            <h3 style="color: var(--primary); margin-bottom: 16px; font-size: 18px;">📊 Market Analysis</h3>
                            <div style="background: var(--bg-input); padding: 20px; border-radius: 12px;">
                                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px;">
                                    <div><strong>Sentiment:</strong> <span style="color: ${market_analysis.sentiment === 'bullish' ? 'var(--success)' : market_analysis.sentiment === 'bearish' ? 'var(--danger)' : 'var(--warning)'}">${market_analysis.sentiment.toUpperCase()}</span></div>
                                    <div><strong>Confidence:</strong> ${market_analysis.confidence}%</div>
                                    <div><strong>GDP:</strong> ${market_analysis.conditions.gdp}</div>
                                    <div><strong>Inflation:</strong> ${market_analysis.conditions.inflation}</div>
                                    <div><strong>Interest Rates:</strong> ${market_analysis.conditions.rates}</div>
                                    <div><strong>Employment:</strong> ${market_analysis.conditions.employment}</div>
                                </div>
                                <p style="color: var(--text-secondary); font-style: italic; margin-top: 12px;">${market_analysis.outlook}</p>
                                <div style="margin-top: 16px;">
                                    <strong>Favored Sectors:</strong> 
                                    ${market_analysis.favored_sectors.map(s => `<span style="background: var(--success); color: white; padding: 2px 8px; border-radius: 4px; margin-right: 4px; font-size: 12px;">${s}</span>`).join('')}
                                </div>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 24px;">
                            <h3 style="color: var(--success); margin-bottom: 16px; font-size: 18px;">📈 Performance Projections</h3>
                            <div style="background: var(--bg-input); padding: 20px; border-radius: 12px;">
                                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                                    <div style="text-align: center; padding: 16px; background: var(--bg-card); border-radius: 8px;">
                                        <div style="font-size: 28px; font-weight: 700; color: var(--success);">${performance.expected_return}%</div>
                                        <div style="color: var(--text-secondary); font-size: 13px;">Expected Return</div>
                                    </div>
                                    <div style="text-align: center; padding: 16px; background: var(--bg-card); border-radius: 8px;">
                                        <div style="font-size: 28px; font-weight: 700; color: var(--warning);">${performance.volatility}%</div>
                                        <div style="color: var(--text-secondary); font-size: 13px;">Volatility</div>
                                    </div>
                                    <div style="text-align: center; padding: 16px; background: var(--bg-card); border-radius: 8px;">
                                        <div style="font-size: 28px; font-weight: 700; color: var(--primary);">${performance.sharpe_ratio}</div>
                                        <div style="color: var(--text-secondary); font-size: 13px;">Sharpe Ratio</div>
                                    </div>
                                </div>
                                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 16px;">
                                    <div style="text-align: center; padding: 12px; background: var(--bg-card); border-radius: 8px;">
                                        <div style="font-size: 20px; font-weight: 600;">${performance.dividend_yield}%</div>
                                        <div style="color: var(--text-secondary); font-size: 12px;">Dividend Yield</div>
                                    </div>
                                    <div style="text-align: center; padding: 12px; background: var(--bg-card); border-radius: 8px;">
                                        <div style="font-size: 20px; font-weight: 600;">${performance.beta}</div>
                                        <div style="color: var(--text-secondary); font-size: 12px;">Portfolio Beta</div>
                                    </div>
                                    <div style="text-align: center; padding: 12px; background: var(--bg-card); border-radius: 8px;">
                                        <div style="font-size: 20px; font-weight: 600; color: var(--danger);">$${performance.var_95.toLocaleString()}</div>
                                        <div style="color: var(--text-secondary); font-size: 12px;">95% VaR</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 24px;">
                            <h3 style="color: var(--warning); margin-bottom: 16px; font-size: 18px;">🎯 Sector Allocation Strategy</h3>
                            <div style="background: var(--bg-input); padding: 20px; border-radius: 12px;">
                                <p style="margin-bottom: 16px;">${sectors.rationale}</p>
                                <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                                    ${sectors.selected.map(s => `
                                        <div style="background: var(--bg-card); padding: 12px 16px; border-radius: 8px; min-width: 120px;">
                                            <div style="font-weight: 600;">${s.name}</div>
                                            <div style="font-size: 24px; font-weight: 700; color: var(--primary);">${s.weight}%</div>
                                            <div style="font-size: 11px; color: var(--text-secondary); text-transform: uppercase;">${s.type}</div>
                                        </div>
                                    `).join('')}
                                </div>
                                <div style="margin-top: 16px; display: flex; gap: 24px;">
                                    <div><strong>Defensive:</strong> ${sectors.defensive_pct}%</div>
                                    <div><strong>Growth:</strong> ${sectors.growth_pct}%</div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 24px;">
                            <h3 style="color: #9334e6; margin-bottom: 16px; font-size: 18px;">💼 Portfolio Summary</h3>
                            <div style="background: var(--bg-input); padding: 20px; border-radius: 12px;">
                                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">
                                    <div><strong>Total Capital:</strong> $${summary.total_capital.toLocaleString()}</div>
                                    <div><strong>Invested:</strong> $${summary.invested.toLocaleString()}</div>
                                    <div><strong>Cash Reserve:</strong> $${summary.cash_reserve.toLocaleString()} (${summary.cash_pct}%)</div>
                                    <div><strong>Positions:</strong> ${summary.num_positions} stocks across ${summary.num_sectors} sectors</div>
                                </div>
                            </div>
                        </div>
                        
                        ${ai_analysis ? `
                        <div style="margin-bottom: 24px;">
                            <h3 style="color: #00bcd4; margin-bottom: 16px; font-size: 18px;">🤖 AI Agent Analysis</h3>
                            <div style="background: var(--bg-input); padding: 20px; border-radius: 12px; white-space: pre-wrap; line-height: 1.7;">
                                ${ai_analysis.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\\n/g, '<br>')}
                            </div>
                        </div>
                        ` : ''}
                    </div>
                `;
                document.getElementById('analysisContent').innerHTML = analysisHtml;
                
                // Build sector data for chart
                const sectorData = {};
                holdings.forEach(h => {
                    sectorData[h.sector] = (sectorData[h.sector] || 0) + h.weight;
                });
                
                // Update charts
                updateCharts(sectorData, holdings);
                
                // Show all tabs
                document.getElementById('emptyState').style.display = 'none';
                document.getElementById('overviewTab').style.display = 'block';
                document.getElementById('holdingsTab').style.display = 'block';
                document.getElementById('analysisTab').style.display = 'block';
                switchTab('overview');
            }
            
            // Update charts with data
            function updateCharts(sectors, stocks) {
                const colors = ['#1a73e8', '#34a853', '#fbbc04', '#ea4335', '#9334e6', '#e91e63', '#00bcd4', '#ff9800'];
                
                // Sector pie chart
                if (sectorChart) sectorChart.destroy();
                const sectorCtx = document.getElementById('sectorChart').getContext('2d');
                sectorChart = new Chart(sectorCtx, {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(sectors),
                        datasets: [{
                            data: Object.values(sectors),
                            backgroundColor: colors.slice(0, Object.keys(sectors).length),
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: { color: '#e8eaed', padding: 12, font: { size: 12 } }
                            }
                        }
                    }
                });
                
                // Composition bar chart
                if (compositionChart) compositionChart.destroy();
                const compCtx = document.getElementById('compositionChart').getContext('2d');
                compositionChart = new Chart(compCtx, {
                    type: 'bar',
                    data: {
                        labels: stocks.map(s => s.symbol),
                        datasets: [{
                            label: 'Weight (%)',
                            data: stocks.map(s => s.weight),
                            backgroundColor: '#1a73e8',
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: 'y',
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { grid: { color: '#3c4043' }, ticks: { color: '#9aa0a6' } },
                            y: { grid: { display: false }, ticks: { color: '#e8eaed' } }
                        }
                    }
                });
            }
            
            // Tab switching
            function switchTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelector(`.tab[onclick="switchTab('${tab}')"]`).classList.add('active');
                
                document.getElementById('overviewTab').style.display = tab === 'overview' ? 'block' : 'none';
                document.getElementById('holdingsTab').style.display = tab === 'holdings' ? 'block' : 'none';
                document.getElementById('analysisTab').style.display = tab === 'analysis' ? 'block' : 'none';
            }
            
            // Loading animation
            let loadingInterval;
            function showLoading() {
                document.getElementById('loadingOverlay').classList.add('active');
                document.getElementById('generateBtn').disabled = true;
                
                const steps = ['step1', 'step2', 'step3', 'step4', 'step5'];
                let currentStep = 0;
                
                loadingInterval = setInterval(() => {
                    if (currentStep > 0) {
                        document.getElementById(steps[currentStep - 1]).classList.remove('active');
                        document.getElementById(steps[currentStep - 1]).classList.add('done');
                    }
                    if (currentStep < steps.length) {
                        document.getElementById(steps[currentStep]).classList.add('active');
                        currentStep++;
                    }
                }, 800);
            }
            
            function hideLoading() {
                clearInterval(loadingInterval);
                document.getElementById('loadingOverlay').classList.remove('active');
                document.getElementById('generateBtn').disabled = false;
                ['step1', 'step2', 'step3', 'step4', 'step5'].forEach(id => {
                    document.getElementById(id).classList.remove('active', 'done');
                });
            }
            
            // Reset form
            function resetForm() {
                portfolioData = null;
                document.getElementById('profileForm').reset();
                document.getElementById('profileSummary').classList.remove('active');
                document.getElementById('emptyState').style.display = 'block';
                document.getElementById('overviewTab').style.display = 'none';
                document.getElementById('holdingsTab').style.display = 'none';
                document.getElementById('analysisTab').style.display = 'none';
                document.getElementById('holdingsTable').innerHTML = '';
                if (sectorChart) sectorChart.destroy();
                if (compositionChart) compositionChart.destroy();
            }
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "portfolio_manager",
        "version": "1.0.0"
    }


@app.get("/api/info")
async def api_info():
    """Get API information."""
    return {
        "name": "Automated Portfolio Manager",
        "version": "1.0.0",
        "endpoints": [
            {"method": "POST", "path": "/api/generate-portfolio", "description": "Generate portfolio"},
            {"method": "GET", "path": "/health", "description": "Health check"}
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
