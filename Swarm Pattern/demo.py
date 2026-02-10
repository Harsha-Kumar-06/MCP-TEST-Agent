"""
Demo script for Financial Portfolio Optimization Swarm
Demonstrates the $50M portfolio rebalancing scenario
"""
import logging
from datetime import datetime, timedelta
from portfolio_swarm.models import Portfolio, Position
from portfolio_swarm.agents import (
    MarketAnalysisAgent, RiskAssessmentAgent, TaxStrategyAgent,
    ESGComplianceAgent, AlgorithmicTradingAgent
)
from portfolio_swarm.communication import CommunicationBus
from portfolio_swarm.orchestrator import SwarmOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)


def create_sample_portfolio() -> Portfolio:
    """Create the $50M sample portfolio with compliance issues"""
    
    # Create positions
    positions = [
        # Technology (36% - OVER LIMIT)
        Position(
            ticker="NVDA",
            shares=10000,
            current_price=500.0,
            cost_basis=450.0,
            acquisition_date=datetime.now() - timedelta(days=330),  # 11 months
            sector="Technology",
            esg_score=78,
            beta=1.8
        ),
        Position(
            ticker="MSFT",
            shares=20000,
            current_price=400.0,
            cost_basis=350.0,
            acquisition_date=datetime.now() - timedelta(days=800),  # Long-term
            sector="Technology",
            esg_score=82,
            beta=1.1
        ),
        Position(
            ticker="AAPL",
            shares=15000,
            current_price=200.0,
            cost_basis=170.0,
            acquisition_date=datetime.now() - timedelta(days=900),  # Long-term
            sector="Technology",
            esg_score=72,
            beta=1.2
        ),
        
        # Healthcare (16%)
        Position(
            ticker="JNJ",
            shares=25000,
            current_price=160.0,
            cost_basis=155.0,
            acquisition_date=datetime.now() - timedelta(days=600),
            sector="Healthcare",
            esg_score=79,
            beta=0.68
        ),
        Position(
            ticker="UNH",
            shares=8000,
            current_price=500.0,
            cost_basis=480.0,
            acquisition_date=datetime.now() - timedelta(days=400),
            sector="Healthcare",
            esg_score=72,
            beta=0.82
        ),
        
        # Financials (14%)
        Position(
            ticker="JPM",
            shares=35000,
            current_price=150.0,
            cost_basis=140.0,
            acquisition_date=datetime.now() - timedelta(days=500),
            sector="Financials",
            esg_score=58,
            beta=1.3
        ),
        Position(
            ticker="BAC",
            shares=50000,
            current_price=40.0,
            cost_basis=38.0,
            acquisition_date=datetime.now() - timedelta(days=450),
            sector="Financials",
            esg_score=62,
            beta=1.4
        ),
        
        # Consumer Staples (12%)
        Position(
            ticker="PG",
            shares=30000,
            current_price=150.0,
            cost_basis=145.0,
            acquisition_date=datetime.now() - timedelta(days=700),
            sector="Consumer Staples",
            esg_score=75,
            beta=0.5
        ),
        Position(
            ticker="KO",
            shares=50000,
            current_price=60.0,
            cost_basis=58.0,
            acquisition_date=datetime.now() - timedelta(days=600),
            sector="Consumer Staples",
            esg_score=68,
            beta=0.6
        ),
        
        # Energy (8%)
        Position(
            ticker="XOM",
            shares=35000,
            current_price=115.0,
            cost_basis=110.0,
            acquisition_date=datetime.now() - timedelta(days=300),
            sector="Energy",
            esg_score=45,
            beta=1.1
        ),
        
        # Industrials (8%)
        Position(
            ticker="CAT",
            shares=15000,
            current_price=265.0,
            cost_basis=255.0,
            acquisition_date=datetime.now() - timedelta(days=400),
            sector="Industrials",
            esg_score=70,
            beta=1.2
        ),
    ]
    
    # Define policy limits
    policy_limits = {
        "technology_limit": 30.0,  # 30% maximum
        "sector_diversification_min": 5.0,  # Min 5% per sector
    }
    
    return Portfolio(
        positions=positions,
        cash=3000000.0,  # $3M cash
        policy_limits=policy_limits
    )


def print_portfolio_summary(portfolio: Portfolio, title: str = "Portfolio Summary"):
    """Print formatted portfolio summary"""
    print("\n" + "="*80)
    print(title)
    print("="*80)
    print(f"\nTotal Value: ${portfolio.total_value:,.0f}")
    print(f"Portfolio Beta: {portfolio.portfolio_beta:.2f}")
    print(f"Average ESG Score: {portfolio.average_esg_score:.1f}")
    
    print("\nSector Allocation:")
    for sector, percentage in sorted(portfolio.sector_allocation.items(), key=lambda x: x[1], reverse=True):
        status = "⚠️ OVER LIMIT" if percentage > 30 else ""
        print(f"  {sector:20s}: {percentage:5.1f}% (${portfolio.total_value * percentage/100:,.0f}) {status}")
    
    print(f"\nCash: ${portfolio.cash:,.0f} ({portfolio.cash/portfolio.total_value*100:.1f}%)")
    
    # Check violations
    violations = portfolio.get_compliance_violations()
    if violations:
        print("\n⚠️  COMPLIANCE VIOLATIONS:")
        for v in violations:
            print(f"  - {v}")
    else:
        print("\n✅ No compliance violations")
    
    print("="*80)


def print_trade_plan(trade_plan, title: str = "Trade Plan"):
    """Print formatted trade plan"""
    print("\n" + "="*80)
    print(title)
    print("="*80)
    
    print("\nProposed Trades:")
    for i, trade in enumerate(trade_plan.trades, 1):
        print(f"\n{i}. {trade.action} {trade.ticker}")
        print(f"   Shares: {trade.shares:,}")
        print(f"   Price: ${trade.estimated_price:.2f}")
        print(f"   Value: ${trade.notional_value:,.0f}")
        print(f"   Rationale: {trade.rationale}")
    
    print(f"\nExecution Summary:")
    print(f"  Total Notional: ${trade_plan.total_notional:,.0f}")
    print(f"  Tax Liability: ${trade_plan.expected_tax_liability:,.0f}")
    print(f"  Execution Cost: ${trade_plan.expected_execution_cost:,.0f}")
    print(f"  Total Cost: ${trade_plan.net_cost:,.0f}")
    print(f"  Timeline: {trade_plan.execution_timeline_days} days")
    
    if trade_plan.projected_portfolio_metrics:
        print(f"\nProjected Metrics:")
        for key, value in trade_plan.projected_portfolio_metrics.items():
            print(f"  {key}: {value}")
    
    print("="*80)


def main():
    """Run the portfolio optimization swarm"""
    
    print("\n" + "#"*80)
    print("# FINANCIAL PORTFOLIO OPTIMIZATION - SWARM PATTERN DEMO")
    print("#"*80)
    
    # Create portfolio
    portfolio = create_sample_portfolio()
    print_portfolio_summary(portfolio, "INITIAL PORTFOLIO STATE")
    
    # Initialize communication bus
    comm_bus = CommunicationBus()
    
    # Create specialized agents
    agents = [
        MarketAnalysisAgent(comm_bus),
        RiskAssessmentAgent(comm_bus),
        TaxStrategyAgent(comm_bus),
        ESGComplianceAgent(comm_bus),
        AlgorithmicTradingAgent(comm_bus)
    ]
    
    print("\n" + "="*80)
    print("AGENT SWARM INITIALIZED")
    print("="*80)
    for agent in agents:
        print(f"  ✓ {agent.agent_type.value.replace('_', ' ').title()} Agent")
    
    # Create orchestrator
    orchestrator = SwarmOrchestrator(
        agents=agents,
        max_iterations=10,
        consensus_threshold=0.6,
        require_unanimous=False
    )
    
    print("\n" + "="*80)
    print("SWARM CONFIGURATION")
    print("="*80)
    print(f"  Max Iterations: {orchestrator.max_iterations}")
    print(f"  Consensus Threshold: {orchestrator.consensus_threshold:.0%}")
    print(f"  Require Unanimous: {orchestrator.require_unanimous}")
    
    # Run swarm optimization
    print("\n" + "#"*80)
    print("# STARTING SWARM OPTIMIZATION PROCESS")
    print("#"*80)
    
    result = orchestrator.run_rebalancing_swarm(portfolio)
    
    # Print results
    print("\n" + "#"*80)
    print("# SWARM OPTIMIZATION COMPLETE")
    print("#"*80)
    
    if result.approved:
        print("\n✅ CONSENSUS ACHIEVED!")
        print(f"   Approval Rate: {result.approval_rate:.1%}")
        print(f"   Iterations Used: {result.iteration + 1}/{orchestrator.max_iterations}")
        
        # Print vote summary
        print("\n" + "="*80)
        print("VOTING SUMMARY")
        print("="*80)
        for vote in result.votes:
            symbol = "✅" if vote.vote.value == "approve" else "❌" if vote.vote.value == "reject" else "⚠️"
            print(f"\n{symbol} {vote.agent_type.value.replace('_', ' ').title()}:")
            print(f"   Vote: {vote.vote.value.upper()}")
            print(f"   Rationale: {vote.rationale}")
            if vote.concerns:
                print(f"   Concerns:")
                for concern in vote.concerns:
                    print(f"     - {concern}")
        
        # Print approved trade plan
        if result.trade_plan:
            print_trade_plan(result.trade_plan, "APPROVED TRADE PLAN")
            
            # Simulate post-trade portfolio
            print("\n" + "="*80)
            print("PROJECTED POST-TRADE PORTFOLIO")
            print("="*80)
            metrics = result.trade_plan.projected_portfolio_metrics
            print(f"\nKey Improvements:")
            for key, value in metrics.items():
                print(f"  {key}: {value}")
    else:
        print("\n❌ NO CONSENSUS REACHED")
        print(f"   Approval Rate: {result.approval_rate:.1%}")
        print(f"   Iterations Used: {result.iteration + 1}/{orchestrator.max_iterations}")
        print("\n   Fallback strategy would be executed (compliance-first approach)")
    
    # Print metrics
    print("\n" + "="*80)
    print("SWARM PERFORMANCE METRICS")
    print("="*80)
    metrics = orchestrator.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print(f"\n  Total Messages Exchanged: {len(orchestrator.comm_bus.messages)}")
    
    # Optional: Print full debate transcript
    print("\n" + "="*80)
    print("Would you like to see the full agent debate transcript? (y/n)")
    print("="*80)
    # In a real implementation, could prompt for user input
    # For demo, we'll skip the full transcript
    
    print("\n" + "#"*80)
    print("# DEMO COMPLETE")
    print("#"*80)


if __name__ == "__main__":
    main()
