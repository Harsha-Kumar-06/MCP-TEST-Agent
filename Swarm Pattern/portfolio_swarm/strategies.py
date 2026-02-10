"""
Optimization Strategies for Portfolio Swarm
Allows users to select their preferred optimization approach after portfolio parsing
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class StrategyType(Enum):
    """Pre-defined optimization strategy types"""
    AGGRESSIVE_GROWTH = "aggressive_growth"
    CONSERVATIVE_INCOME = "conservative_income"
    BALANCED = "balanced"
    TAX_EFFICIENT = "tax_efficient"
    ESG_FOCUSED = "esg_focused"
    RISK_MINIMIZATION = "risk_minimization"
    SECTOR_ROTATION = "sector_rotation"
    DIVIDEND_GROWTH = "dividend_growth"
    CUSTOM = "custom"


@dataclass
class OptimizationStrategy:
    """
    Defines the optimization strategy parameters that guide agent behavior
    
    After portfolio parsing, users can select a strategy to customize
    how the swarm agents approach the optimization problem.
    """
    strategy_type: StrategyType
    name: str
    description: str
    
    # Target allocations
    target_sector_weights: Dict[str, float] = field(default_factory=dict)
    target_beta: float = 1.0
    target_esg_score: float = 70.0
    
    # Constraints
    max_position_size: float = 0.20  # Max % of portfolio in single position
    max_sector_concentration: float = 0.30  # Max % in any sector
    min_cash_reserve: float = 0.05  # Minimum cash to maintain
    
    # Risk parameters
    max_portfolio_beta: float = 1.5
    min_portfolio_beta: float = 0.5
    volatility_target: float = 0.15  # 15% annualized volatility
    max_drawdown_tolerance: float = 0.20  # 20% max acceptable drawdown
    
    # Tax considerations
    prefer_long_term_gains: bool = True
    harvest_losses: bool = True
    tax_loss_threshold: float = -0.10  # 10% loss to trigger harvesting
    
    # ESG preferences
    min_esg_score: int = 60
    exclude_sectors: List[str] = field(default_factory=list)
    
    # Income preferences
    min_dividend_yield: float = 0.0
    prefer_dividend_growth: bool = False
    
    # Trading preferences
    max_turnover: float = 0.30  # Max 30% annual turnover
    min_trade_size: float = 1000.0  # Minimum trade in dollars
    urgency_level: str = "normal"  # "low", "normal", "high"
    
    # Custom priorities (1-10 scale)
    priorities: Dict[str, int] = field(default_factory=dict)


# Pre-defined strategy templates
STRATEGY_TEMPLATES: Dict[StrategyType, OptimizationStrategy] = {
    
    StrategyType.AGGRESSIVE_GROWTH: OptimizationStrategy(
        strategy_type=StrategyType.AGGRESSIVE_GROWTH,
        name="Aggressive Growth",
        description="Maximize capital appreciation with higher risk tolerance. Focus on growth sectors and momentum.",
        target_beta=1.3,
        max_portfolio_beta=2.0,
        min_portfolio_beta=0.8,
        volatility_target=0.25,
        max_drawdown_tolerance=0.35,
        target_sector_weights={
            "Technology": 0.35,
            "Healthcare": 0.20,
            "Consumer Discretionary": 0.15,
        },
        min_esg_score=50,
        max_turnover=0.50,
        prefer_long_term_gains=False,
        priorities={
            "growth": 10,
            "risk": 3,
            "income": 2,
            "tax_efficiency": 4,
            "esg": 3,
        }
    ),
    
    StrategyType.CONSERVATIVE_INCOME: OptimizationStrategy(
        strategy_type=StrategyType.CONSERVATIVE_INCOME,
        name="Conservative Income",
        description="Prioritize stable income with capital preservation. Focus on dividends and low volatility.",
        target_beta=0.7,
        max_portfolio_beta=1.0,
        min_portfolio_beta=0.4,
        volatility_target=0.10,
        max_drawdown_tolerance=0.12,
        target_sector_weights={
            "Utilities": 0.20,
            "Consumer Staples": 0.20,
            "Healthcare": 0.15,
            "Financials": 0.15,
        },
        min_dividend_yield=0.03,
        prefer_dividend_growth=True,
        max_turnover=0.15,
        min_cash_reserve=0.10,
        priorities={
            "growth": 3,
            "risk": 9,
            "income": 10,
            "tax_efficiency": 7,
            "esg": 5,
        }
    ),
    
    StrategyType.BALANCED: OptimizationStrategy(
        strategy_type=StrategyType.BALANCED,
        name="Balanced",
        description="Balanced approach between growth and income. Moderate risk with diversification.",
        target_beta=1.0,
        max_portfolio_beta=1.3,
        min_portfolio_beta=0.7,
        volatility_target=0.15,
        max_drawdown_tolerance=0.20,
        max_sector_concentration=0.25,
        priorities={
            "growth": 6,
            "risk": 6,
            "income": 5,
            "tax_efficiency": 6,
            "esg": 6,
        }
    ),
    
    StrategyType.TAX_EFFICIENT: OptimizationStrategy(
        strategy_type=StrategyType.TAX_EFFICIENT,
        name="Tax Efficient",
        description="Minimize tax impact while achieving reasonable returns. Prioritize long-term gains and loss harvesting.",
        target_beta=1.0,
        prefer_long_term_gains=True,
        harvest_losses=True,
        tax_loss_threshold=-0.07,
        max_turnover=0.10,
        urgency_level="low",
        priorities={
            "growth": 5,
            "risk": 6,
            "income": 4,
            "tax_efficiency": 10,
            "esg": 5,
        }
    ),
    
    StrategyType.ESG_FOCUSED: OptimizationStrategy(
        strategy_type=StrategyType.ESG_FOCUSED,
        name="ESG Focused",
        description="Prioritize environmental, social, and governance factors. Exclude controversial sectors.",
        target_beta=1.0,
        target_esg_score=80.0,
        min_esg_score=75,
        exclude_sectors=["Tobacco", "Weapons", "Gambling", "Oil & Gas"],
        priorities={
            "growth": 5,
            "risk": 6,
            "income": 4,
            "tax_efficiency": 5,
            "esg": 10,
        }
    ),
    
    StrategyType.RISK_MINIMIZATION: OptimizationStrategy(
        strategy_type=StrategyType.RISK_MINIMIZATION,
        name="Risk Minimization",
        description="Minimize portfolio risk and volatility. Focus on defensive positions and hedging.",
        target_beta=0.5,
        max_portfolio_beta=0.8,
        min_portfolio_beta=0.3,
        volatility_target=0.08,
        max_drawdown_tolerance=0.10,
        max_position_size=0.10,
        max_sector_concentration=0.20,
        min_cash_reserve=0.15,
        target_sector_weights={
            "Utilities": 0.25,
            "Consumer Staples": 0.25,
            "Healthcare": 0.20,
        },
        priorities={
            "growth": 2,
            "risk": 10,
            "income": 6,
            "tax_efficiency": 5,
            "esg": 5,
        }
    ),
    
    StrategyType.SECTOR_ROTATION: OptimizationStrategy(
        strategy_type=StrategyType.SECTOR_ROTATION,
        name="Sector Rotation",
        description="Actively rotate between sectors based on economic cycle. Higher turnover with tactical allocation.",
        target_beta=1.1,
        max_turnover=0.60,
        urgency_level="high",
        priorities={
            "growth": 8,
            "risk": 5,
            "income": 3,
            "tax_efficiency": 3,
            "esg": 4,
        }
    ),
    
    StrategyType.DIVIDEND_GROWTH: OptimizationStrategy(
        strategy_type=StrategyType.DIVIDEND_GROWTH,
        name="Dividend Growth",
        description="Focus on companies with growing dividends. Balance current yield with dividend growth potential.",
        target_beta=0.9,
        min_dividend_yield=0.02,
        prefer_dividend_growth=True,
        max_turnover=0.20,
        priorities={
            "growth": 6,
            "risk": 6,
            "income": 9,
            "tax_efficiency": 6,
            "esg": 5,
        }
    ),
}


def get_strategy(strategy_type: StrategyType) -> OptimizationStrategy:
    """Get a pre-defined strategy by type"""
    if strategy_type == StrategyType.CUSTOM:
        raise ValueError("Use create_custom_strategy() for custom strategies")
    return STRATEGY_TEMPLATES.get(strategy_type, STRATEGY_TEMPLATES[StrategyType.BALANCED])


def create_custom_strategy(
    name: str,
    description: str,
    base_strategy: StrategyType = StrategyType.BALANCED,
    **kwargs
) -> OptimizationStrategy:
    """
    Create a custom strategy based on a template with overrides
    
    Args:
        name: Custom strategy name
        description: Strategy description
        base_strategy: Base template to start from
        **kwargs: Override any strategy parameter
        
    Returns:
        OptimizationStrategy with custom parameters
    """
    # Start with base template
    if base_strategy != StrategyType.CUSTOM:
        base = STRATEGY_TEMPLATES[base_strategy]
        # Create new strategy with base values
        strategy_dict = {
            "strategy_type": StrategyType.CUSTOM,
            "name": name,
            "description": description,
            "target_sector_weights": dict(base.target_sector_weights),
            "target_beta": base.target_beta,
            "target_esg_score": base.target_esg_score,
            "max_position_size": base.max_position_size,
            "max_sector_concentration": base.max_sector_concentration,
            "min_cash_reserve": base.min_cash_reserve,
            "max_portfolio_beta": base.max_portfolio_beta,
            "min_portfolio_beta": base.min_portfolio_beta,
            "volatility_target": base.volatility_target,
            "max_drawdown_tolerance": base.max_drawdown_tolerance,
            "prefer_long_term_gains": base.prefer_long_term_gains,
            "harvest_losses": base.harvest_losses,
            "tax_loss_threshold": base.tax_loss_threshold,
            "min_esg_score": base.min_esg_score,
            "exclude_sectors": list(base.exclude_sectors),
            "min_dividend_yield": base.min_dividend_yield,
            "prefer_dividend_growth": base.prefer_dividend_growth,
            "max_turnover": base.max_turnover,
            "min_trade_size": base.min_trade_size,
            "urgency_level": base.urgency_level,
            "priorities": dict(base.priorities),
        }
    else:
        # Start with defaults
        strategy_dict = {
            "strategy_type": StrategyType.CUSTOM,
            "name": name,
            "description": description,
        }
    
    # Apply overrides
    strategy_dict.update(kwargs)
    
    return OptimizationStrategy(**strategy_dict)


def list_available_strategies() -> List[Dict]:
    """Get list of available strategy templates for UI display"""
    strategies = []
    for strategy_type, strategy in STRATEGY_TEMPLATES.items():
        strategies.append({
            "type": strategy_type.value,
            "name": strategy.name,
            "description": strategy.description,
            "target_beta": strategy.target_beta,
            "risk_level": _get_risk_level(strategy),
            "priorities": strategy.priorities,
        })
    return strategies


def _get_risk_level(strategy: OptimizationStrategy) -> str:
    """Determine risk level label from strategy parameters"""
    if strategy.max_drawdown_tolerance >= 0.30:
        return "High"
    elif strategy.max_drawdown_tolerance >= 0.18:
        return "Medium"
    else:
        return "Low"


def strategy_to_prompt(strategy: OptimizationStrategy) -> str:
    """Convert strategy to natural language for agent prompts"""
    priorities_str = ", ".join([
        f"{k}: {v}/10" for k, v in sorted(
            strategy.priorities.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
    ])
    
    prompt = f"""
OPTIMIZATION STRATEGY: {strategy.name}
{strategy.description}

KEY PARAMETERS:
- Target Portfolio Beta: {strategy.target_beta} (range: {strategy.min_portfolio_beta} - {strategy.max_portfolio_beta})
- Volatility Target: {strategy.volatility_target:.0%}
- Maximum Drawdown Tolerance: {strategy.max_drawdown_tolerance:.0%}
- Maximum Position Size: {strategy.max_position_size:.0%} of portfolio
- Maximum Sector Concentration: {strategy.max_sector_concentration:.0%}
- Minimum Cash Reserve: {strategy.min_cash_reserve:.0%}

TAX CONSIDERATIONS:
- Prefer Long-Term Gains: {strategy.prefer_long_term_gains}
- Harvest Tax Losses: {strategy.harvest_losses}
- Maximum Turnover: {strategy.max_turnover:.0%}

ESG REQUIREMENTS:
- Minimum ESG Score: {strategy.min_esg_score}
- Excluded Sectors: {', '.join(strategy.exclude_sectors) if strategy.exclude_sectors else 'None'}

INCOME PREFERENCES:
- Minimum Dividend Yield: {strategy.min_dividend_yield:.1%}
- Focus on Dividend Growth: {strategy.prefer_dividend_growth}

PRIORITY WEIGHTS (1-10):
{priorities_str}

Please incorporate these strategy parameters into your analysis and recommendations.
"""
    return prompt
