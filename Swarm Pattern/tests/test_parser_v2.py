"""Test the new v2 parser"""
import sys
sys.path.insert(0, r'c:\Users\Harsha Kumar\Desktop\DRAVYN\Agents\Swarm Pattern')

from portfolio_swarm.text_parser_v2 import parse_portfolio_text

# Test with the actual complex input
test_input = """Portfolio Crisis Analysis - Multi-Scenario Optimization

500 MSFT shares at 420, bought for 350
150 NVDA shares at 880, bought for 420  
400 GOOGL shares at 165, bought for 140
300 AAPL shares at 185, bought for 155
100 META shares at 475, bought for 380

200 JPM shares at 195, bought for 150
130 V shares at 285, bought for 240

60 UNH shares at 520, bought for 485
90 JNJ shares at 160, bought for 155

300 KO shares at 62, bought for 58
180 PG shares at 165, bought for 155

150 BABA shares at 95, bought for 115
35 TSM shares at 145, bought for 130
120 XOM shares at 108, bought for 95

Cash 50000
Tech limit 40%
ESG minimum 55
"""

print("="*70)
print("TESTING NEW PARSER V2")
print("="*70)

try:
    portfolio = parse_portfolio_text(test_input)
    print(f"\n✅ SUCCESS! Parsed {len(portfolio.positions)} positions")
    print(f"Cash: ${portfolio.cash:,.0f}")
    print(f"Policy Limits: {portfolio.policy_limits}")
    print(f"\nPositions:")
    print(f"{'Ticker':<8}{'Shares':>8}{'Current':>10}{'Cost':>10}{'Gain %':>10}{'Value':>15}{'Sector':<12}")
    print("-" * 75)
    
    total_value = 0
    for p in portfolio.positions:
        value = p.shares * p.current_price
        gain = ((p.current_price - p.cost_basis) / p.cost_basis * 100) if p.cost_basis else 0
        print(f"{p.ticker:<8}{p.shares:>8}{p.current_price:>10.2f}{p.cost_basis:>10.2f}{gain:>9.1f}%${value:>14,.0f} {p.sector:<12}")
        total_value += value
    
    total_value += portfolio.cash
    print("-" * 75)
    print(f"{'TOTAL':<8}{'':<8}{'':<10}{'':<10}{'':<10}${total_value:>14,.0f}")
    
    # Verify specific positions
    print(f"\n{'='*70}")
    print("VERIFICATION:")
    print("="*70)
    
    msft = next((p for p in portfolio.positions if p.ticker == 'MSFT'), None)
    if msft:
        print(f"✅ MSFT: {msft.shares} shares @ ${msft.current_price} (expected: 500 @ $420)")
        if msft.shares == 500 and msft.current_price == 420.0:
            print("   ✅ CORRECT!")
        else:
            print("   ❌ INCORRECT!")
    
    nvda = next((p for p in portfolio.positions if p.ticker == 'NVDA'), None)
    if nvda:
        print(f"✅ NVDA: {nvda.shares} shares @ ${nvda.current_price} (expected: 150 @ $880)")
        if nvda.shares == 150 and nvda.current_price == 880.0:
            print("   ✅ CORRECT!")
        else:
            print("   ❌ INCORRECT!")
    
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
