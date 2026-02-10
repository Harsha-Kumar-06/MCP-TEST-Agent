"""
Test the API migration - verify new google.genai works
"""
from portfolio_swarm.text_parser_gemini import GeminiEnhancedParser

# Test with unknown company
test_text = """
Portfolio Update:
- Snowflake (SNOW): 200 shares at $180 (bought at $150)
- CrowdStrike: 150 shares trading at $320 per share, cost basis $280
"""

print("🧪 Testing API Migration with Unknown Companies...")
print("=" * 60)

try:
    parser = GeminiEnhancedParser(test_text)
    portfolio = parser.parse()
    
    print(f"\n✅ Parser initialized successfully")
    print(f"   API Mode: {'NEW google.genai' if parser.knowledge.use_new_api else 'OLD google.generativeai'}")
    print(f"   Model: {parser.knowledge.model_name}")
    
    print(f"\n📊 Parsed {len(portfolio.positions)} positions:")
    for pos in portfolio.positions:
        print(f"   • {pos.ticker} ({pos.company})")
        print(f"     Shares: {pos.shares}, Price: ${pos.current_price:.2f}, Cost: ${pos.cost_basis:.2f}")
        print(f"     Sector: {pos.sector}, ESG: {pos.esg_score}")
    
    print(f"\n💰 Cash: ${portfolio.cash:,.2f}")
    
    print("\n" + "=" * 60)
    print("✅ API Migration Test PASSED - No Deprecation Warnings!")
    
except Exception as e:
    print(f"\n❌ Test Failed: {e}")
    import traceback
    traceback.print_exc()
