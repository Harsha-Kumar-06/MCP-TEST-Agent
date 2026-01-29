"""Test Web Search API (Google + DuckDuckGo fallback)"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from tools.web_search import web_search, duckduckgo_search, format_search_results_for_agent

async def test_search():
    print('Testing Web Search (with DuckDuckGo fallback)...')
    print('='*50)
    
    # Use unified search (tries Google, falls back to DuckDuckGo)
    result = await web_search('climate change effects 2024', num_results=5)
    
    if result.get('success'):
        source = result.get('source', 'Unknown')
        print(f'✅ SUCCESS via {source}! Found', len(result.get('results', [])), 'results')
        print()
        formatted = format_search_results_for_agent(result)
        print(formatted)
    else:
        print('❌ FAILED:', result.get('error'))
        
        # Try DuckDuckGo directly
        print('\n' + '='*50)
        print('Trying DuckDuckGo directly...')
        ddg_result = await duckduckgo_search('climate change effects', num_results=5)
        
        if ddg_result.get('success'):
            print(f'✅ DuckDuckGo SUCCESS! Found', len(ddg_result.get('results', [])), 'results')
            formatted = format_search_results_for_agent(ddg_result)
            print(formatted)
        else:
            print('❌ DuckDuckGo also failed:', ddg_result.get('error'))

if __name__ == "__main__":
    asyncio.run(test_search())
