"""
Data models for portfolio management and agent communication
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class AgentType(Enum):
    MARKET_ANALYSIS = "market_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    TAX_STRATEGY = "tax_strategy"
    ESG_COMPLIANCE = "esg_compliance"
    ALGORITHMIC_TRADING = "algorithmic_trading"


class VoteType(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class Position:
    """Represents a portfolio position"""
    ticker: str
    shares: int
    current_price: float
    cost_basis: float
    acquisition_date: datetime
    sector: str
    esg_score: int
    beta: float
    
    @property
    def market_value(self) -> float:
        return self.shares * self.current_price
    
    @property
    def unrealized_gain(self) -> float:
        return (self.current_price - self.cost_basis) * self.shares
    
    @property
    def is_long_term(self) -> bool:
        """Position held > 1 year"""
        if self.acquisition_date is None:
            return False  # Assume short-term if date unknown (conservative)
        days_held = (datetime.now() - self.acquisition_date).days
        return days_held > 365


@dataclass
class Portfolio:
    """Complete portfolio state"""
    positions: List[Position]
    cash: float
    policy_limits: Dict[str, float] = field(default_factory=dict)
    
    @property
    def total_value(self) -> float:
        return sum(p.market_value for p in self.positions) + self.cash
    
    @property
    def sector_allocation(self) -> Dict[str, float]:
        """Returns sector allocation as percentages"""
        sector_values = {}
        for position in self.positions:
            sector_values[position.sector] = sector_values.get(position.sector, 0) + position.market_value
        
        total = self.total_value
        return {sector: (value / total * 100) for sector, value in sector_values.items()}
    
    @property
    def portfolio_beta(self) -> float:
        """Weighted average beta"""
        total_value = self.total_value
        weighted_beta = sum(p.market_value / total_value * p.beta for p in self.positions)
        return weighted_beta
    
    @property
    def average_esg_score(self) -> float:
        """Weighted average ESG score"""
        total_value = self.total_value
        weighted_esg = sum(p.market_value / total_value * p.esg_score for p in self.positions)
        return weighted_esg
    
    def get_compliance_violations(self) -> List[str]:
        """Check policy violations"""
        violations = []
        sector_alloc = self.sector_allocation
        
        for sector, percentage in sector_alloc.items():
            limit_key = f"{sector.lower()}_limit"
            if limit_key in self.policy_limits:
                limit = self.policy_limits[limit_key]
                if percentage > limit:
                    violations.append(f"{sector} at {percentage:.1f}% exceeds {limit}% limit")
        
        return violations


@dataclass
class Trade:
    """Represents a proposed trade"""
    action: str  # "BUY" or "SELL"
    ticker: str
    shares: int
    estimated_price: float
    rationale: str
    
    @property
    def notional_value(self) -> float:
        return self.shares * self.estimated_price


@dataclass
class TradePlan:
    """Complete rebalancing trade plan"""
    trades: List[Trade]
    expected_tax_liability: float
    expected_execution_cost: float
    execution_timeline_days: int
    projected_portfolio_metrics: Dict[str, float]
    
    @property
    def total_notional(self) -> float:
        return sum(t.notional_value for t in self.trades)
    
    @property
    def net_cost(self) -> float:
        """Total cost including taxes and execution"""
        return self.expected_tax_liability + self.expected_execution_cost


@dataclass
class AgentAnalysis:
    """Analysis output from a single agent"""
    agent_type: AgentType
    findings: str
    recommendation: str
    conviction: int  # 1-10
    concerns: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentProposal:
    """Proposed solution from an agent"""
    agent_type: AgentType
    trade_plan: TradePlan
    rationale: str
    conviction: int


@dataclass
class AgentVote:
    """Vote on a proposal"""
    agent_type: AgentType
    vote: VoteType
    rationale: str
    concerns: List[str] = field(default_factory=list)


@dataclass
class Message:
    """Inter-agent communication message"""
    from_agent: AgentType
    to_agent: Optional[AgentType]  # None = broadcast
    content: str
    iteration: int
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str = "debate"  # debate, proposal, vote, question


@dataclass
class ConsensusResult:
    """Result of consensus voting"""
    approved: bool
    trade_plan: Optional[TradePlan]
    votes: List[AgentVote]
    approval_rate: float
    iteration: int
    
    @property
    def unanimous(self) -> bool:
        return all(v.vote == VoteType.APPROVE for v in self.votes)
