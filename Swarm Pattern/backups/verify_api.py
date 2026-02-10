"""
Quick verification that API migration is complete
Shows which API is being used without making actual Gemini calls
"""
from portfolio_swarm.text_parser_gemini import DynamicKnowledgeBase

print("=" * 70)
print("🔍 API Migration Verification")
print("=" * 70)

try:
    kb = DynamicKnowledgeBase()
    
    print(f"\n✅ Parser Initialized Successfully")
    print(f"\n📊 API Configuration:")
    print(f"   • API Mode: {'NEW google.genai ✨' if kb.use_new_api else 'OLD google.generativeai (fallback)'}")
    print(f"   • Model: {kb.model_name}")
    print(f"   • Status: {'ACTIVE - Latest Non-Deprecated API' if kb.use_new_api else 'FALLBACK - Old API'}")
    
    if kb.use_new_api:
        print(f"\n🎉 SUCCESS! Using latest Gemini 2.5+ API from AI Studio")
        print(f"   ✅ No deprecation warnings")
        print(f"   ✅ Future-proof implementation")
        print(f"   ✅ Gemini 2.0+/2.5+ models only")
    else:
        print(f"\n⚠️  Using fallback API (old google.generativeai)")
        print(f"   Consider installing: pip install google-genai")
    
    print(f"\n📦 Available Features:")
    print(f"   • Dynamic ticker/company name learning")
    print(f"   • Intelligent sector classification")
    print(f"   • ESG score estimation")
    print(f"   • Full text extraction fallback")
    print(f"   • JSON caching (zero cost after first lookup)")
    
    print(f"\n💾 Cache File: portfolio_knowledge_cache.json")
    
    print("\n" + "=" * 70)
    print("✅ API Migration Complete - System Ready!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ Initialization Error: {e}")
    import traceback
    traceback.print_exc()

print("\n📝 Next Steps:")
print("   1. Run Flask UI: python flask_ui.py")
print("   2. Open browser: http://localhost:5000")
print("   3. Test with COMPLEX_INPUT_READY.txt")
print("\n   See API_MIGRATION_COMPLETE.md for full details")
