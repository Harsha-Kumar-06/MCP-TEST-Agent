"""
Quick unit test for proposal adaptation logic (no API calls)
"""
from portfolio_swarm.models import Portfolio, Position, TradePlan, Trade, AgentAnalysis
from portfolio_swarm.agents import RiskAssessmentAgent, MarketAnalysisAgent
from portfolio_swarm.communication import CommunicationBus
from portfolio_swarm.strategies import get_strategy, StrategyType


def create_test_portfolio():
    """Create a portfolio with compliance violations"""
    from datetime import datetime
    positions = [
        Position(ticker='NVDA', shares=10000, cost_basis=420, current_price=875, 
                 acquisition_date=datetime(2025, 1, 15), sector='Technology', esg_score=68, beta=1.95),
        Position(ticker='MSFT', shares=5000, cost_basis=350, current_price=410, 
                 acquisition_date=datetime(2024, 6, 1), sector='Technology', esg_score=82, beta=1.1),
        Position(ticker='XOM', shares=8000, cost_basis=95, current_price=108, 
                 acquisition_date=datetime(2024, 3, 1), sector='Energy', esg_score=42, beta=1.15),
        Position(ticker='JPM', shares=6000, cost_basis=140, current_price=185, 
                 acquisition_date=datetime(2024, 1, 1), sector='Finance', esg_score=58, beta=1.3),
    ]
    return Portfolio(
        positions=positions,
        cash=500000,
        policy_limits={'technology_limit': 30.0}
    )


def test_proposal_adaptation():
    """Test that proposals adapt based on iteration and feedback"""
    print("="*60)
    print("TEST: Proposal Adaptation Logic")
    print("="*60)
    
    portfolio = create_test_portfolio()
    comm_bus = CommunicationBus()
    
    print(f"\nPortfolio: ${portfolio.total_value:,.0f}")
    print(f"Tech allocation: {portfolio.sector_allocation.get('Technology', 0):.1f}%")
    print(f"Violations: {portfolio.get_compliance_violations()}")
    
    # Test Risk Assessment Agent
    risk_agent = RiskAssessmentAgent(comm_bus)
    risk_agent.set_strategy(get_strategy(StrategyType.BALANCED))
    
    print("\n--- Risk Assessment Agent Proposals ---")
    
    prev_notional = float('inf')
    for iteration in range(5):
        # Set iteration
        risk_agent.set_iteration(iteration)
        risk_agent.max_iterations = 5
        
        # Simulate rejection feedback (as if Algo rejected for large trades)
        if iteration > 0:
            risk_agent.set_rejection_feedback([
                "algorithmic_trading: Execution score 6/100 too risky. 3 large, 3 illiquid trades"
            ])
        
        # Generate proposal
        proposal = risk_agent.propose_solution(portfolio, [])
        
        if proposal:
            notional = proposal.trade_plan.total_notional
            num_trades = len(proposal.trade_plan.trades)
            change = ((notional - prev_notional) / prev_notional * 100) if prev_notional != float('inf') else 0
            
            # Check if notional is decreasing
            status = "✓ SMALLER" if notional < prev_notional else "⚠ SAME/LARGER"
            
            print(f"  Iter {iteration+1}: {num_trades} trades, ${notional:,.0f} notional {status}")
            print(f"           Rationale: {proposal.rationale}")
            
            # Show trades
            for t in proposal.trade_plan.trades[:3]:
                print(f"           - {t.action} {t.ticker}: {t.shares} shares (${t.notional_value:,.0f})")
            
            prev_notional = notional
        else:
            print(f"  Iter {iteration+1}: No proposal generated")
    
    # Test Market Analysis Agent
    market_agent = MarketAnalysisAgent(comm_bus)
    market_agent.set_strategy(get_strategy(StrategyType.BALANCED))
    
    print("\n--- Market Analysis Agent Proposals ---")
    
    prev_notional = float('inf')
    for iteration in range(5):
        market_agent.set_iteration(iteration)
        market_agent.max_iterations = 5
        
        if iteration > 0:
            market_agent.set_rejection_feedback([
                "algorithmic_trading: Execution too costly"
            ])
        
        proposal = market_agent.propose_solution(portfolio, [])
        
        if proposal:
            notional = proposal.trade_plan.total_notional
            num_trades = len(proposal.trade_plan.trades)
            
            status = "✓ SMALLER" if notional < prev_notional else "⚠ SAME/LARGER"
            print(f"  Iter {iteration+1}: {num_trades} trades, ${notional:,.0f} notional {status}")
            print(f"           Conviction: {proposal.conviction}/10")
            
            prev_notional = notional
        else:
            print(f"  Iter {iteration+1}: No proposal generated")
    
    print("\n" + "="*60)
    print("✅ Proposal adaptation test complete!")
    print("="*60)


def test_voting_scores():
    """Test that voting produces varied scores based on data"""
    print("\n" + "="*60)
    print("TEST: Voting Score Logic")
    print("="*60)
    
    from portfolio_swarm.agents import (
        MarketAnalysisAgent, RiskAssessmentAgent, TaxStrategyAgent,
        ESGComplianceAgent, AlgorithmicTradingAgent
    )
    
    portfolio = create_test_portfolio()
    comm_bus = CommunicationBus()
    
    # Create a proposal to vote on
    trades = [
        Trade(action="SELL", ticker="NVDA", shares=2000, estimated_price=875, 
              rationale="Reduce tech"),
        Trade(action="BUY", ticker="XOM", shares=5000, estimated_price=108, 
              rationale="Add energy"),
    ]
    proposal = TradePlan(
        trades=trades,
        expected_tax_liability=50000,
        expected_execution_cost=500,
        execution_timeline_days=1,
        projected_portfolio_metrics={}
    )
    
    print(f"\nProposal: {len(trades)} trades, ${proposal.total_notional:,.0f} notional")
    
    agents = [
        ("Market Analysis", MarketAnalysisAgent(comm_bus)),
        ("Risk Assessment", RiskAssessmentAgent(comm_bus)),
        ("Tax Strategy", TaxStrategyAgent(comm_bus)),
        ("ESG Compliance", ESGComplianceAgent(comm_bus)),
        ("Algorithmic Trading", AlgorithmicTradingAgent(comm_bus)),
    ]
    
    print("\n--- Agent Votes ---")
    for name, agent in agents:
        agent.set_iteration(0)
        agent.max_iterations = 5
        
        vote = agent.vote_on_proposal(proposal, portfolio)
        
        status = "✅" if vote.vote.value == "approve" else "❌"
        print(f"  {status} {name}: {vote.vote.value.upper()}")
        print(f"     Rationale: {vote.rationale}")
    
    print("\n" + "="*60)
    print("✅ Voting score test complete!")
    print("="*60)


if __name__ == "__main__":
    test_proposal_adaptation()
    test_voting_scores()
