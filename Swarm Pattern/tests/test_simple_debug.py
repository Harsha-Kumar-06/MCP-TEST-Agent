"""Simple debug test for parser"""
from portfolio_swarm.text_parser import parse_portfolio_text

# Simplest possible test  
simple_test = """
500 MSFT at 420 bought at 350
150 NVDA at 880 bought at 420
Cash 50000
"""

print("Testing:", simple_test)
print("\n" + "="*60)

try:
    portfolio = parse_portfolio_text(simple_test)
    print(f"✅ Parsed {len(portfolio.positions)} positions\n")
    
    for pos in portfolio.positions:
        print(f"{pos.ticker}: {pos.shares} shares")
        print(f"  Current: ${pos.current_price}")
        print(f"  Cost: ${pos.cost_basis}")
        print(f"  Expected: Current=$420, Cost=$350" if pos.ticker == "MSFT" else f"  Expected: Current=$880, Cost=$420")
        print()
        
except Exception as e:
    print(f"❌ Error: {e}")
