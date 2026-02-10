"""
Example: Using Different Input Formats
Demonstrates how to load portfolios from various file formats
"""
from portfolio_swarm.input_parser import PortfolioParser
from portfolio_swarm.orchestrator import SwarmOrchestrator
from portfolio_swarm.models import VoteType
from portfolio_swarm.agents import (
    MarketAnalysisAgent,
    RiskAssessmentAgent,
    TaxStrategyAgent,
    ESGComplianceAgent,
    AlgorithmicTradingAgent
)
from portfolio_swarm.communication import CommunicationBus


def run_from_file(file_path: str):
    """
    Load portfolio from file and run swarm optimization
    
    Args:
        file_path: Path to input file (CSV, JSON, YAML, Excel)
    """
    print(f"\n{'='*80}")
    print(f"Loading portfolio from: {file_path}")
    print(f"{'='*80}\n")
    
    # Step 1: Parse input file
    parser = PortfolioParser()
    portfolio = parser.parse_file(file_path)
    
    print(f"Portfolio loaded successfully!")
    print(f"  - Positions: {len(portfolio.positions)}")
    print(f"  - Total value: ${portfolio.total_value:,.0f}")
    print(f"  - Cash: ${portfolio.cash:,.0f}")
    print(f"  - Sector allocation:")
    for sector, pct in portfolio.sector_allocation.items():
        print(f"      {sector}: {pct:.1f}%")
    
    # Step 2: Validate portfolio
    warnings = parser.validate_portfolio(portfolio)
    if warnings:
        print(f"\n⚠️  Validation warnings:")
        for w in warnings:
            print(f"    {w}")
    
    # Step 3: Initialize swarm agents
    print(f"\n{'='*80}")
    print("Initializing AI Swarm Agents...")
    print(f"{'='*80}\n")
    
    bus = CommunicationBus()
    agents = [
        MarketAnalysisAgent(bus),
        RiskAssessmentAgent(bus),
        TaxStrategyAgent(bus),
        ESGComplianceAgent(bus),
        AlgorithmicTradingAgent(bus)
    ]
    
    orchestrator = SwarmOrchestrator(
        agents=agents,
        max_iterations=5,
        consensus_threshold=0.6
    )
    
    # Step 4: Run optimization
    print("Starting swarm optimization...\n")
    result = orchestrator.run_rebalancing_swarm(portfolio)
    
    # Step 5: Display results
    print(f"\n{'='*80}")
    print("OPTIMIZATION RESULTS")
    print(f"{'='*80}\n")
    
    consensus_status = "YES" if result.approved else "NO"
    print(f"Consensus reached: {consensus_status}")
    print(f"Iterations: {result.iteration + 1}")
    print(f"Approval rate: {result.approval_rate:.1%}")
    
    if result.trade_plan:
        print(f"\nRecommended trades: {len(result.trade_plan.trades)}")
        print(f"Estimated tax liability: ${result.trade_plan.expected_tax_liability:,.0f}")
        print(f"Execution cost: ${result.trade_plan.expected_execution_cost:,.0f}")
        
        if result.trade_plan.trades:
            print(f"\nTrade details:")
            for trade in result.trade_plan.trades[:5]:  # Show first 5
                action = trade.action
                print(f"  {action:4s} {abs(trade.shares):5d} shares of {trade.ticker:5s} "
                      f"@ ${trade.estimated_price:.2f} - {trade.rationale[:50]}...")
    
    print(f"\nAgent votes:")
    for vote in result.votes:
        status = "APPROVED" if vote.vote == VoteType.APPROVE else "REJECTED"
        print(f"  {vote.agent_type.value:20s}: {status:12s}")
        if vote.rationale:
            print(f"    -> {vote.rationale[:80]}...")
    
    return result


def compare_multiple_files():
    """Compare results from different input files"""
    print("\n" + "="*80)
    print("COMPARING MULTIPLE INPUT FORMATS")
    print("="*80 + "\n")
    
    files = [
        "samples/sample_portfolio.csv",
        "samples/sample_portfolio.json",
        "samples/sample_portfolio.yaml"
    ]
    
    results = {}
    
    for file in files:
        try:
            result = run_from_file(file)
            results[file] = result
        except Exception as e:
            print(f"\n❌ Error processing {file}: {e}\n")
    
    # Compare results
    if len(results) > 1:
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80 + "\n")
        
        for file, result in results.items():
            consensus_status = "YES" if result.approved else "NO"
            print(f"{file}:")
            print(f"  Consensus: {consensus_status}")
            print(f"  Approval: {result.approval_rate:.1%}")
            print(f"  Trades: {len(result.trade_plan.trades) if result.trade_plan else 0}")
            print()


def interactive_file_selection():
    """Let user select which file to use"""
    import os
    
    print("\n" + "="*80)
    print("PORTFOLIO INPUT FILE SELECTOR")
    print("="*80 + "\n")
    
    # List available sample files
    samples_dir = "samples"
    if os.path.exists(samples_dir):
        files = [f for f in os.listdir(samples_dir) if f.startswith('sample_portfolio')]
        
        if files:
            print("Available input files:\n")
            for i, file in enumerate(files, 1):
                size = os.path.getsize(os.path.join(samples_dir, file))
                print(f"  {i}. {file:30s} ({size:,} bytes)")
            
            print(f"\n  {len(files)+1}. Compare all files")
            print(f"  {len(files)+2}. Exit")
            
            try:
                choice = input(f"\nSelect file (1-{len(files)+2}): ").strip()
                choice = int(choice)
                
                if 1 <= choice <= len(files):
                    file_path = os.path.join(samples_dir, files[choice-1])
                    run_from_file(file_path)
                elif choice == len(files) + 1:
                    compare_multiple_files()
                else:
                    print("Exiting...")
            except (ValueError, IndexError):
                print("Invalid choice")
        else:
            print("No sample files found in samples/ directory")
    else:
        print("samples/ directory not found")


def export_templates():
    """Export empty templates in all formats"""
    print("\n" + "="*80)
    print("EXPORTING INPUT TEMPLATES")
    print("="*80 + "\n")
    
    parser = PortfolioParser()
    
    templates = {
        'csv': 'samples/template.csv',
        'json': 'samples/template.json',
        'yaml': 'samples/template.yaml'
    }
    
    for format, path in templates.items():
        try:
            parser.export_template(format, path)
            print(f"✓ Exported {format.upper()} template to: {path}")
        except Exception as e:
            print(f"✗ Error exporting {format.upper()}: {e}")
    
    print("\nTemplates exported! Edit them and use as input files.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # File path provided as argument
        file_path = sys.argv[1]
        run_from_file(file_path)
    else:
        # Interactive mode
        print("\n" + "="*80)
        print("PORTFOLIO SWARM - FILE INPUT DEMO")
        print("="*80 + "\n")
        print("Options:")
        print("  1. Run with specific file")
        print("  2. Interactive file selector")
        print("  3. Compare all sample files")
        print("  4. Export blank templates")
        print("  5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            file_path = input("Enter file path: ").strip()
            run_from_file(file_path)
        elif choice == "2":
            interactive_file_selection()
        elif choice == "3":
            compare_multiple_files()
        elif choice == "4":
            export_templates()
        else:
            print("Exiting...")
