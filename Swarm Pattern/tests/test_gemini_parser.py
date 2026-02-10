"""Test Gemini-enhanced parser with unknown companies"""
import sys
sys.path.insert(0, r'c:\Users\Harsha Kumar\Desktop\DRAVYN\Agents\Swarm Pattern')

from portfolio_swarm.text_parser_gemini import parse_portfolio_text

# Test with companies NOT in the static mappings
test_unknown = """
Portfolio with emerging tech stocks:

500 Snowflake shares at 150, bought for 120
200 Palantir shares at 25, bought for 18
150 CrowdStrike at 280, bought for 200
100 Datadog at 120, bought for 95
80 MongoDB at 380, bought for 320

Plus some established ones:
300 Microsoft at 420, bought for 350
150 NVDA at 880, bought for 420

Cash 100000
Tech limit 50
ESG minimum 60
"""

print("="*70)
print("TESTING GEMINI-ENHANCED DYNAMIC PARSER")
print("="*70)
print("\nInput includes companies NOT in static mappings:")
print("- Snowflake, Palantir, CrowdStrike, Datadog, MongoDB")
print("\nGemini will dynamically learn their tickers and sectors!")
print("="*70)

try:
    portfolio = parse_portfolio_text(test_unknown)
    print(f"\n✅ SUCCESS! Parsed {len(portfolio.positions)} positions")
    print(f"Cash: ${portfolio.cash:,.0f}")
    print(f"Policy Limits: {portfolio.policy_limits}\n")
    
    print(f"{'Ticker':<10}{'Shares':>8}{'Current':>10}{'Cost':>10}{'Sector':<15}{'ESG':>5}")
    print("-" * 70)
    
    for p in portfolio.positions:
        print(f"{p.ticker:<10}{p.shares:>8}{p.current_price:>10.2f}{p.cost_basis:>10.2f}{p.sector:<15}{p.esg_score:>5}")
    
    print("\n" + "="*70)
    print("RESULTS:")
    print("="*70)
    
    # Check if unknown companies were identified
    unknown_tickers = ['SNOW', 'PLTR', 'CRWD', 'DDOG', 'MDB']
    found_unknown = [p.ticker for p in portfolio.positions if p.ticker in unknown_tickers]
    
    if found_unknown:
        print(f"✨ Gemini successfully identified: {', '.join(found_unknown)}")
        print(f"✨ These mappings are now cached for future use!")
    else:
        print("⚠️  Unknown companies not found - check Gemini API key")
    
    # Check sectors were assigned
    for p in portfolio.positions:
        if p.sector != 'Other':
            print(f"✅ {p.ticker} assigned to {p.sector} sector")
    
    print("\n💡 The learned mappings are saved to 'portfolio_knowledge_cache.json'")
    print("   Future parses will be instant (no API calls needed)!")
    
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
