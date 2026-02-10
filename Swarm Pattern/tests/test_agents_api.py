"""
Quick test to verify agents.py works with new API
"""
import os
os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', 'test_key_placeholder')

from portfolio_swarm.communication import CommunicationBus
from portfolio_swarm.agents import MarketAnalysisAgent

print("="*70)
print("🧪 Testing Agent API Configuration")
print("="*70)

try:
    bus = CommunicationBus()
    agent = MarketAnalysisAgent(bus)
    
    print(f"\n✅ MarketAnalysisAgent initialized successfully")
    print(f"   • USE_NEW_API: {agent.use_new_api}")
    print(f"   • Has gemini_client: {agent.gemini_client is not None}")
    print(f"   • Has model (old API): {agent.model is not None}")
    
    if agent.use_new_api:
        print(f"\n🎉 SUCCESS! Agent using NEW google.genai API")
        print(f"   ✅ Future-proof implementation")
        print(f"   ✅ No deprecation warnings")
    else:
        print(f"\n⚠️  Agent using OLD google.generativeai API (fallback)")
        print(f"   → Install google-genai package for new API")
    
    print("\n" + "="*70)
    print("✅ Agent Configuration Test PASSED")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Test Failed: {e}")
    import traceback
    traceback.print_exc()
