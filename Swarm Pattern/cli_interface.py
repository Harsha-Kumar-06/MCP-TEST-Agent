"""
Interactive CLI for Portfolio Swarm System
User-friendly interface to input portfolio data and view results
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict
from portfolio_swarm.models import Portfolio, Position
from portfolio_swarm.agents import (
    MarketAnalysisAgent, RiskAssessmentAgent, TaxStrategyAgent,
    ESGComplianceAgent, AlgorithmicTradingAgent
)
from portfolio_swarm.communication import CommunicationBus
from portfolio_swarm.orchestrator import SwarmOrchestrator


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_section(title: str):
    """Print section header"""
    print(f"\n{title}")
    print("-" * 40)


def get_user_input(prompt: str, default: str = None, input_type: type = str):
    """Get input from user with validation"""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip() or default
        else:
            user_input = input(f"{prompt}: ").strip()
        
        try:
            if input_type == int:
                return int(user_input)
            elif input_type == float:
                return float(user_input)
            elif input_type == bool:
                return user_input.lower() in ['y', 'yes', 'true', '1']
            else:
                return user_input
        except ValueError:
            print(f"❌ Invalid input. Please enter a valid {input_type.__name__}.")


def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not response:
        return default
    return response in ['y', 'yes']


def input_position() -> Position:
    """Interactively input a portfolio position"""
    print_section("Enter Position Details")
    
    ticker = get_user_input("Ticker symbol (e.g., AAPL)").upper()
    shares = get_user_input("Number of shares", input_type=int)
    current_price = get_user_input("Current price per share", input_type=float)
    cost_basis = get_user_input("Cost basis (original price)", input_type=float)
    
    # Acquisition date
    print("\nAcquisition date:")
    print("  1. Enter manually (YYYY-MM-DD)")
    print("  2. Enter days ago")
    date_choice = get_user_input("Choice [1-2]", "2")
    
    if date_choice == "1":
        date_str = get_user_input("Date (YYYY-MM-DD)", "2024-01-01")
        acquisition_date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        days_ago = get_user_input("Days ago", "400", int)
        acquisition_date = datetime.now() - timedelta(days=days_ago)
    
    # Sector
    print("\nSelect sector:")
    sectors = ["Technology", "Healthcare", "Financials", "Consumer Staples", 
               "Energy", "Industrials", "Utilities", "Real Estate", "Materials"]
    for i, sector in enumerate(sectors, 1):
        print(f"  {i}. {sector}")
    sector_choice = get_user_input(f"Choice [1-{len(sectors)}]", "1", int)
    sector = sectors[sector_choice - 1]
    
    # ESG score
    esg_score = get_user_input("ESG score (0-100)", "70", int)
    
    # Beta
    beta = get_user_input("Beta (market sensitivity)", "1.0", float)
    
    return Position(
        ticker=ticker,
        shares=shares,
        current_price=current_price,
        cost_basis=cost_basis,
        acquisition_date=acquisition_date,
        sector=sector,
        esg_score=esg_score,
        beta=beta
    )


def input_portfolio() -> Portfolio:
    """Interactively build a portfolio"""
    print_header("PORTFOLIO INPUT")
    
    positions = []
    
    # Add positions
    while True:
        position = input_position()
        positions.append(position)
        
        print(f"\n✓ Added {position.ticker}: {position.shares} shares @ ${position.current_price}")
        
        if not get_yes_no("\nAdd another position?", False):
            break
    
    # Cash
    print_section("Cash Balance")
    cash = get_user_input("Cash balance ($)", "1000000", float)
    
    # Policy limits
    print_section("Policy Limits (Optional)")
    policy_limits = {}
    
    if get_yes_no("Set sector limits?", True):
        tech_limit = get_user_input("Technology sector limit (%)", "30", float)
        policy_limits["technology_limit"] = tech_limit
        
        if get_yes_no("Set limits for other sectors?", False):
            for sector in ["healthcare", "financials", "energy"]:
                limit = get_user_input(f"{sector.title()} limit (%)", "25", float)
                policy_limits[f"{sector}_limit"] = limit
    
    return Portfolio(
        positions=positions,
        cash=cash,
        policy_limits=policy_limits
    )


def configure_swarm() -> Dict:
    """Configure swarm parameters"""
    print_header("SWARM CONFIGURATION")
    
    print_section("Consensus Rules")
    max_iterations = get_user_input("Max iterations", "10", int)
    consensus_threshold = get_user_input("Consensus threshold (0.0-1.0)", "0.6", float)
    require_unanimous = get_yes_no("Require unanimous approval?", False)
    
    return {
        "max_iterations": max_iterations,
        "consensus_threshold": consensus_threshold,
        "require_unanimous": require_unanimous
    }


def display_results(result, orchestrator):
    """Display swarm results"""
    print_header("SWARM RESULTS")
    
    if result.approved:
        print("\n🎉 CONSENSUS ACHIEVED!")
        print(f"   Approval Rate: {result.approval_rate:.1%}")
        print(f"   Iterations: {result.iteration + 1}/{orchestrator.max_iterations}")
        
        # Vote summary
        print_section("Agent Votes")
        for vote in result.votes:
            symbol = "✅" if vote.vote.value == "approve" else "❌" if vote.vote.value == "reject" else "⚠️"
            agent_name = vote.agent_type.value.replace('_', ' ').title()
            print(f"{symbol} {agent_name:20s} - {vote.vote.value.upper()}")
            print(f"   {vote.rationale[:70]}...")
        
        # Trade plan
        if result.trade_plan:
            print_section("Approved Trade Plan")
            print(f"\nTotal Trades: {len(result.trade_plan.trades)}")
            
            for i, trade in enumerate(result.trade_plan.trades, 1):
                print(f"\n{i}. {trade.action} {trade.ticker}")
                print(f"   Shares: {trade.shares:,}")
                print(f"   Value: ${trade.notional_value:,.2f}")
                print(f"   Reason: {trade.rationale[:60]}...")
            
            print(f"\n{'─'*40}")
            print(f"Tax Liability:     ${result.trade_plan.expected_tax_liability:,.2f}")
            print(f"Execution Cost:    ${result.trade_plan.expected_execution_cost:,.2f}")
            print(f"Total Cost:        ${result.trade_plan.net_cost:,.2f}")
            print(f"Timeline:          {result.trade_plan.execution_timeline_days} days")
            print(f"{'─'*40}")
            
            # Projected metrics
            if result.trade_plan.projected_portfolio_metrics:
                print_section("Projected Portfolio Metrics")
                for key, value in result.trade_plan.projected_portfolio_metrics.items():
                    print(f"  {key:25s}: {value}")
    
    else:
        print("\n❌ NO CONSENSUS REACHED")
        print(f"   Approval Rate: {result.approval_rate:.1%}")
        print(f"   Iterations Used: {result.iteration + 1}/{orchestrator.max_iterations}")
        print("\n   A compliance-first fallback strategy would be executed.")


def save_results(result, orchestrator, filename: str):
    """Save results to file"""
    with open(filename, 'w') as f:
        f.write("SWARM OPTIMIZATION RESULTS\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Consensus: {'ACHIEVED' if result.approved else 'NOT REACHED'}\n")
        f.write(f"Approval Rate: {result.approval_rate:.1%}\n")
        f.write(f"Iterations: {result.iteration + 1}\n\n")
        
        if result.trade_plan:
            f.write("TRADE PLAN:\n")
            f.write("-"*40 + "\n")
            for trade in result.trade_plan.trades:
                f.write(f"{trade.action} {trade.ticker}: {trade.shares} shares @ ${trade.estimated_price}\n")
        
        f.write("\n\nFULL DEBATE TRANSCRIPT:\n")
        f.write("-"*40 + "\n")
        f.write(orchestrator.get_debate_summary())
    
    print(f"\n✓ Results saved to: {filename}")


def main():
    """Main CLI application"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("╔" + "═"*78 + "╗")
    print("║" + " "*15 + "FINANCIAL PORTFOLIO SWARM SYSTEM" + " "*31 + "║")
    print("║" + " "*20 + "Interactive CLI Interface" + " "*33 + "║")
    print("╚" + "═"*78 + "╝")
    
    # Main menu
    while True:
        print_header("MAIN MENU")
        print("\n1. Run optimization with custom portfolio")
        print("2. Run optimization with sample portfolio")
        print("3. View documentation")
        print("4. Exit")
        
        choice = get_user_input("\nSelect option [1-4]", "1")
        
        if choice == "4":
            print("\n👋 Goodbye!")
            break
        
        elif choice == "3":
            print_header("DOCUMENTATION")
            print("\n📖 Available documentation files:")
            print("  • README.md - Complete overview")
            print("  • QUICKSTART.md - Quick start guide")
            print("  • ARCHITECTURE.md - System architecture")
            print("  • financial_portfolio_optimization.md - Use case details")
            print("\nRun: python demo.py to see a working example")
            input("\nPress Enter to continue...")
            continue
        
        elif choice == "1":
            # Custom portfolio
            portfolio = input_portfolio()
        
        elif choice == "2":
            # Sample portfolio (from demo.py)
            from demo import create_sample_portfolio
            portfolio = create_sample_portfolio()
            print("\n✓ Loaded sample $50M portfolio with compliance violation")
        
        else:
            print("❌ Invalid choice")
            continue
        
        # Display portfolio summary
        print_header("PORTFOLIO SUMMARY")
        print(f"\nTotal Value: ${portfolio.total_value:,.2f}")
        print(f"Cash: ${portfolio.cash:,.2f}")
        print(f"Positions: {len(portfolio.positions)}")
        print(f"\nSector Allocation:")
        for sector, pct in sorted(portfolio.sector_allocation.items(), key=lambda x: x[1], reverse=True):
            print(f"  {sector:20s}: {pct:5.1f}%")
        
        violations = portfolio.get_compliance_violations()
        if violations:
            print("\n⚠️  Compliance Violations:")
            for v in violations:
                print(f"  • {v}")
        
        if not get_yes_no("\nProceed with optimization?", True):
            continue
        
        # Configure swarm
        config = configure_swarm()
        
        # Initialize swarm
        print_header("INITIALIZING SWARM")
        comm_bus = CommunicationBus()
        agents = [
            MarketAnalysisAgent(comm_bus),
            RiskAssessmentAgent(comm_bus),
            TaxStrategyAgent(comm_bus),
            ESGComplianceAgent(comm_bus),
            AlgorithmicTradingAgent(comm_bus)
        ]
        
        orchestrator = SwarmOrchestrator(
            agents=agents,
            max_iterations=config["max_iterations"],
            consensus_threshold=config["consensus_threshold"],
            require_unanimous=config["require_unanimous"]
        )
        
        print("\n✓ Agents initialized:")
        for agent in agents:
            print(f"  • {agent.agent_type.value.replace('_', ' ').title()}")
        
        input("\nPress Enter to start optimization...")
        
        # Run optimization
        print_header("RUNNING SWARM OPTIMIZATION")
        print("\n⏳ This may take a few moments...\n")
        
        result = orchestrator.run_rebalancing_swarm(portfolio)
        
        # Display results
        display_results(result, orchestrator)
        
        # Save results
        if get_yes_no("\nSave results to file?", True):
            filename = get_user_input("Filename", f"swarm_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            save_results(result, orchestrator, filename)
        
        # Show debate transcript
        if get_yes_no("\nView full debate transcript?", False):
            print_header("DEBATE TRANSCRIPT")
            print(orchestrator.get_debate_summary())
            input("\nPress Enter to continue...")
        
        # Continue or exit
        if not get_yes_no("\nRun another optimization?", False):
            print("\n👋 Thank you for using the Portfolio Swarm System!")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
