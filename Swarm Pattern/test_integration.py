"""
Integration test - quick swarm run without AI
"""
from datetime import datetime
from portfolio_swarm.models import Portfolio, Position
from portfolio_swarm.orchestrator import SwarmOrchestrator
from portfolio_swarm.agents import (
    MarketAnalysisAgent, RiskAssessmentAgent, TaxStrategyAgent,
    ESGComplianceAgent, AlgorithmicTradingAgent
)
from portfolio_swarm.communication import CommunicationBus
from portfolio_swarm.strategies import get_strategy, StrategyType


def test_swarm_integration():
    """Test full swarm integration without AI calls"""
    print("="*70)
    print("INTEGRATION TEST: Full Swarm (No AI)")
    print("="*70)
    
    # Create portfolio with violations
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
    
    portfolio = Portfolio(positions=positions, cash=500000, 
                         policy_limits={'technology_limit': 30.0})
    
    print(f"\nPortfolio: ${portfolio.total_value:,.0f}")
    print(f"Tech allocation: {portfolio.sector_allocation.get('Technology', 0):.1f}%")
    print(f"Violations: {portfolio.get_compliance_violations()}")
    
    # Create agents
    comm_bus = CommunicationBus()
    agents = [
        MarketAnalysisAgent(comm_bus),
        RiskAssessmentAgent(comm_bus),
        TaxStrategyAgent(comm_bus),
        ESGComplianceAgent(comm_bus),
        AlgorithmicTradingAgent(comm_bus),
    ]
    
    strategy = get_strategy(StrategyType.BALANCED)
    for agent in agents:
        agent.set_strategy(strategy)
    
    # Create orchestrator - LOW iterations, HIGH consensus to force adaptation
    orchestrator = SwarmOrchestrator(
        agents=agents,
        min_iterations=2,
        max_iterations=6,
        consensus_threshold=1.0,  # 100% required - forces iteration
        strategy=strategy
    )
    
    print(f"\nRunning swarm (100% consensus, max 6 iterations)...")
    print("-"*50)
    
    result = orchestrator.run_rebalancing_swarm(portfolio)
    
    # Results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    print(f"Approved: {result.approved}")
    print(f"Approval Rate: {result.approval_rate:.0%}")
    print(f"Iterations: {len(orchestrator.iteration_history)}")
    
    if result.trade_plan and result.trade_plan.trades:
        print(f"\nFinal Trades ({len(result.trade_plan.trades)}):")
        for t in result.trade_plan.trades:
            print(f"  {t.action} {t.ticker}: {t.shares} @ ${t.estimated_price:.2f} (${t.notional_value:,.0f})")
        print(f"Total Notional: ${result.trade_plan.total_notional:,.0f}")
    
    print("\n--- ITERATION HISTORY ---")
    for i, iter_data in enumerate(orchestrator.iteration_history):
        votes = iter_data['votes']
        approves = sum(1 for v in votes if v['vote'] == 'approve')
        rejects = sum(1 for v in votes if v['vote'] == 'reject')
        
        proposal = iter_data.get('proposal', {})
        notional = proposal.get('total_notional', 0)
        from_agent = proposal.get('from_agent', 'Unknown')
        
        status = "✅ CONSENSUS" if iter_data['consensus_reached'] else f"({iter_data['approval_rate']*100:.0f}%)"
        
        print(f"\nIteration {iter_data['iteration']}:")
        print(f"  Proposal: {from_agent}, ${notional:,.0f} notional")
        print(f"  Votes: {approves}✓ {rejects}✗ {status}")
        
        # Show rejecting agents
        for v in votes:
            if v['vote'] == 'reject':
                print(f"    ❌ {v['agent']}: {v['rationale'][:50]}...")
    
    print("\n" + "="*70)
    print("✅ Integration test complete!")
    print("="*70)


if __name__ == "__main__":
    test_swarm_integration()
