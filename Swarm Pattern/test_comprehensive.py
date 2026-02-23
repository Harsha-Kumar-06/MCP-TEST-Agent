"""
Comprehensive test script for Portfolio Swarm System
Tests multiple portfolios, strategies, and consensus thresholds
"""
from portfolio_swarm.models import Portfolio, Position
from portfolio_swarm.orchestrator import SwarmOrchestrator
from portfolio_swarm.agents import (
    MarketAnalysisAgent, RiskAssessmentAgent, TaxStrategyAgent, 
    ESGComplianceAgent, AlgorithmicTradingAgent
)
from portfolio_swarm.communication import CommunicationBus
from portfolio_swarm.strategies import get_strategy, StrategyType
from datetime import datetime
import time


def create_sample_portfolio():
    """Standard diversified portfolio"""
    positions = [
        Position(ticker='NVDA', shares=2200, cost_basis=420, current_price=875, 
                 acquisition_date=datetime(2025, 1, 15), sector='Technology', esg_score=68, beta=1.95),
        Position(ticker='MSFT', shares=8000, cost_basis=350, current_price=410, 
                 acquisition_date=datetime(2024, 6, 1), sector='Technology', esg_score=82, beta=1.1),
        Position(ticker='AAPL', shares=10000, cost_basis=165, current_price=185, 
                 acquisition_date=datetime(2024, 3, 1), sector='Technology', esg_score=75, beta=1.2),
        Position(ticker='JNJ', shares=15000, cost_basis=155, current_price=162, 
                 acquisition_date=datetime(2023, 1, 1), sector='Healthcare', esg_score=72, beta=0.7),
        Position(ticker='XOM', shares=12000, cost_basis=95, current_price=108, 
                 acquisition_date=datetime(2024, 3, 1), sector='Energy', esg_score=42, beta=1.15),
        Position(ticker='JPM', shares=8000, cost_basis=140, current_price=185, 
                 acquisition_date=datetime(2024, 1, 1), sector='Finance', esg_score=58, beta=1.3),
    ]
    return Portfolio(
        positions=positions,
        cash=500000,
        policy_limits={'technology_limit': 30.0, 'min_esg_score': 60}
    )


def create_crisis_portfolio():
    """High concentration, multiple violations"""
    positions = [
        Position(ticker='NVDA', shares=25000, cost_basis=420, current_price=875, 
                 acquisition_date=datetime(2026, 1, 8), sector='Technology', esg_score=68, beta=1.95),
        Position(ticker='META', shares=12000, cost_basis=485, current_price=512, 
                 acquisition_date=datetime(2025, 12, 20), sector='Technology', esg_score=52, beta=1.4),
        Position(ticker='TSLA', shares=5000, cost_basis=280, current_price=245, 
                 acquisition_date=datetime(2025, 11, 1), sector='Consumer', esg_score=45, beta=2.3),
        Position(ticker='XOM', shares=15000, cost_basis=95, current_price=108, 
                 acquisition_date=datetime(2024, 6, 1), sector='Energy', esg_score=42, beta=1.15),
    ]
    return Portfolio(
        positions=positions,
        cash=800000,
        policy_limits={'technology_limit': 25.0, 'min_esg_score': 70, 'max_beta': 1.2}
    )


def create_agents():
    """Create fresh set of agents"""
    comm_bus = CommunicationBus()
    return [
        MarketAnalysisAgent(comm_bus),
        RiskAssessmentAgent(comm_bus),
        TaxStrategyAgent(comm_bus),
        ESGComplianceAgent(comm_bus),
        AlgorithmicTradingAgent(comm_bus),
    ]


def run_test(name, portfolio, strategy_type, consensus, min_iter=2, max_iter=5):
    """Run a single test scenario"""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    
    strategy = get_strategy(strategy_type)
    agents = create_agents()
    
    # Set strategy on all agents
    for agent in agents:
        agent.set_strategy(strategy)
    
    print(f"Portfolio: {len(portfolio.positions)} positions, ${portfolio.total_value:,.0f}")
    print(f"Strategy: {strategy.name} ({strategy.star_rating})")
    print(f"Consensus: {consensus:.0%}")
    print(f"Iterations: min={min_iter}, max={max_iter}")
    
    violations = portfolio.get_compliance_violations()
    if violations:
        print(f"Violations: {len(violations)}")
        for v in violations[:3]:
            print(f"  - {v}")
    
    orchestrator = SwarmOrchestrator(
        agents=agents,
        min_iterations=min_iter,
        max_iterations=max_iter,
        consensus_threshold=consensus,
        strategy=strategy
    )
    
    start = time.time()
    result = orchestrator.run_rebalancing_swarm(portfolio)
    elapsed = time.time() - start
    
    print(f"\n--- RESULT ({elapsed:.1f}s) ---")
    print(f"Approved: {result.approved}")
    print(f"Approval Rate: {result.approval_rate:.0%}")
    print(f"Iterations Run: {len(orchestrator.iteration_history)}")
    
    if result.trade_plan and result.trade_plan.trades:
        print(f"Trades: {len(result.trade_plan.trades)}")
        print(f"Total Notional: ${result.trade_plan.total_notional:,.0f}")
    
    # Show iteration progression
    print("\n--- ITERATION PROGRESSION ---")
    for iter_data in orchestrator.iteration_history:
        votes = iter_data['votes']
        approves = sum(1 for v in votes if v['vote'] == 'approve')
        rejects = sum(1 for v in votes if v['vote'] == 'reject')
        proposal = iter_data.get('proposal', {})
        notional = proposal.get('total_notional', 0)
        
        status = "✅ CONSENSUS" if iter_data['consensus_reached'] else f"({result.approval_rate*100:.0f}%)"
        print(f"  Iter {iter_data['iteration']}: {approves}✓ {rejects}✗ | "
              f"${notional:,.0f} notional | {status}")
        
        # Show why rejected
        if rejects > 0:
            for v in votes:
                if v['vote'] == 'reject':
                    print(f"    ❌ {v['agent']}: {v['rationale'][:60]}...")
    
    return result


def main():
    print("\n" + "="*70)
    print("🧪 PORTFOLIO SWARM COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    # TEST 1: Sample Portfolio + Balanced
    sample = create_sample_portfolio()
    run_test(
        "Sample Portfolio + Balanced (60% consensus)",
        sample, StrategyType.BALANCED, 0.6, min_iter=2, max_iter=4
    )
    
    # TEST 2: Sample Portfolio + ESG Focused (stricter)
    sample2 = create_sample_portfolio()
    run_test(
        "Sample Portfolio + ESG Focused (80% consensus)",
        sample2, StrategyType.ESG_FOCUSED, 0.8, min_iter=2, max_iter=5
    )
    
    # TEST 3: Crisis Portfolio + Risk Minimization (100% consensus)
    crisis = create_crisis_portfolio()
    run_test(
        "Crisis Portfolio + Risk Minimization (100% consensus)",
        crisis, StrategyType.RISK_MINIMIZATION, 1.0, min_iter=3, max_iter=8
    )
    
    # TEST 4: Crisis Portfolio + Aggressive Growth (55% consensus)
    crisis2 = create_crisis_portfolio()
    run_test(
        "Crisis Portfolio + Aggressive Growth (55% consensus)",
        crisis2, StrategyType.AGGRESSIVE_GROWTH, 0.55, min_iter=2, max_iter=5
    )
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70)


if __name__ == "__main__":
    main()
