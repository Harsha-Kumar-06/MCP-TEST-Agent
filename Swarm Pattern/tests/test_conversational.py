"""Test conversational format specifically"""
from portfolio_swarm.text_parser_v2 import parse_portfolio_text

test = """
I own 500 Microsoft shares at $420 bought at $350.
Also holding 150 NVIDIA at $880 purchased at $420.
Plus 400 Alphabet at $165 bought at $140.
Cash balance is $50,000.
"""

print("Testing conversational format:")
print("="*70)
print(test)
print("="*70)

try:
    portfolio = parse_portfolio_text(test)
    print(f"\n✅ Parsed {len(portfolio.positions)} positions")
    print(f"Cash: ${portfolio.cash:,.0f}\n")
    
    expected = {
        'MSFT': (500, 420, 350),
        'NVDA': (150, 880, 420),
        'GOOGL': (400, 165, 140),
    }
    
    for pos in portfolio.positions:
        exp_shares, exp_current, exp_cost = expected.get(pos.ticker, (0, 0, 0))
        match = "✅" if (pos.shares == exp_shares and pos.current_price == exp_current and pos.cost_basis == exp_cost) else "❌"
        
        print(f"{match} {pos.ticker}")
        print(f"   Got:      {pos.shares} shares @ ${pos.current_price} (cost ${pos.cost_basis})")
        print(f"   Expected: {exp_shares} shares @ ${exp_current} (cost ${exp_cost})")
        print()
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
