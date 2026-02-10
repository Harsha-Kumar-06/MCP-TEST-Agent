"""Test flexible text parser with various input formats"""
from portfolio_swarm.text_parser import parse_portfolio_text

# Test Case 1: Natural conversational style
test1 = """
I have a tech-heavy portfolio. I own 500 Microsoft shares at $420 bought at $350.
Also holding 150 NVIDIA at $880 purchased at $420. Plus 400 Alphabet at $165 bought at $140.
Cash balance is $50,000.
"""

# Test Case 2: Simple list format  
test2 = """
500 MSFT at $420 bought at $350
150 NVDA at $880 bought at $420  
400 GOOGL at $165 bought at $140
300 AAPL at $185 bought at $155
Cash $50000
"""

# Test Case 3: Mixed detailed narrative
test3 = """
Portfolio Analysis Request:

My technology holdings include 500 Microsoft (MSFT) currently trading at $420, 
which I bought at $350. I also have 150 shares of NVIDIA at $880 per share,
purchased at $420. Additionally, I'm holding 400 Alphabet shares, current price
$165, cost basis $140.

For healthcare exposure, I own 60 UnitedHealth at $520, bought at $485.

Cash available: $50,000
Technology sector limit: 40%
"""

# Test Case 4: Parentheses format
test4 = """
Current positions:
- Microsoft (MSFT): 500 shares at $420, cost $350
- NVIDIA (NVDA): 150 shares at $880, purchased $420
- Alphabet (GOOGL): 400 shares, current $165, basis $140
Cash: $50k
"""

test_cases = [
    ("Conversational", test1),
    ("Simple List", test2),
    ("Detailed Narrative", test3),
    ("Parentheses Format", test4)
]

print("="*70)
print("FLEXIBLE TEXT PARSER TEST")
print("="*70)

for name, text in test_cases:
    print(f"\n{'='*70}")
    print(f"Test: {name}")
    print(f"{'='*70}")
    print(f"Input Text:\n{text[:200]}...")
    
    try:
        portfolio = parse_portfolio_text(text)
        print(f"\n✅ SUCCESS! Parsed {len(portfolio.positions)} positions")
        print(f"Cash: ${portfolio.cash:,.0f}")
        print(f"\nPositions found:")
        for pos in portfolio.positions:
            value = pos.shares * pos.current_price
            gain = (pos.current_price - pos.cost_basis) / pos.cost_basis * 100
            print(f"  {pos.ticker:6} {pos.shares:>5} shares @ ${pos.current_price:>7.2f} "
                  f"(cost: ${pos.cost_basis:>7.2f}, gain: {gain:>6.1f}%, value: ${value:>12,.0f})")
        
        total_value = sum(p.shares * p.current_price for p in portfolio.positions) + portfolio.cash
        print(f"\n  Total Portfolio Value: ${total_value:,.0f}")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*70}")
print("Test Complete!")
print(f"{'='*70}\n")
