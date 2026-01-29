"""
Web Search Tool for ADK Agents
Supports Google Custom Search API and DuckDuckGo (free fallback)
"""
import os
import aiohttp
from typing import Optional

# Google Custom Search API endpoint
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
# DuckDuckGo API (free, no key required)
DUCKDUCKGO_URL = "https://api.duckduckgo.com/"


async def duckduckgo_search(query: str, num_results: int = 5) -> dict:
    """
    Search using DuckDuckGo HTML search (FREE, no API key needed)
    
    Args:
        query: Search query string
        num_results: Number of results to return
        
    Returns:
        dict with search results
    """
    # Use HTML search directly (more reliable)
    return await duckduckgo_html_search(query, num_results)


async def duckduckgo_html_search(query: str, num_results: int = 5) -> dict:
    """
    Scrape DuckDuckGo HTML search results (more comprehensive)
    """
    url = "https://html.duckduckgo.com/html/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data={"q": query}, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Simple HTML parsing for results
                    results = []
                    
                    # Find result blocks
                    import re
                    
                    # Extract links and snippets
                    link_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
                    snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]+(?:<[^>]+>[^<]*</[^>]+>)*[^<]*)</a>'
                    
                    links = re.findall(link_pattern, html)
                    snippets = re.findall(snippet_pattern, html)
                    
                    for i, (link, title) in enumerate(links[:num_results]):
                        snippet = snippets[i] if i < len(snippets) else ""
                        # Clean HTML from snippet
                        snippet = re.sub(r'<[^>]+>', '', snippet)
                        
                        results.append({
                            "title": title.strip(),
                            "link": link,
                            "snippet": snippet.strip(),
                            "source": "DuckDuckGo"
                        })
                    
                    return {
                        "success": True,
                        "query": query,
                        "total_results": len(results),
                        "results": results,
                        "source": "DuckDuckGo"
                    }
                else:
                    return {"success": False, "error": f"DuckDuckGo HTML Error: {response.status}"}
                    
    except Exception as e:
        return {"success": False, "error": f"DuckDuckGo HTML search failed: {str(e)}"}


async def google_search(
    query: str,
    num_results: int = 5,
    search_type: Optional[str] = None
) -> dict:
    """
    Search Google using Custom Search API
    
    Args:
        query: Search query string
        num_results: Number of results (max 10 per request)
        search_type: None for web search, "image" for image search
        
    Returns:
        dict with search results or error
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_CX")  # Custom Search Engine ID
    
    if not api_key:
        return {"error": "GOOGLE_API_KEY not configured"}
    
    if not cx:
        return {"error": "GOOGLE_SEARCH_CX not configured. Create one at https://programmablesearchengine.google.com/"}
    
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": min(num_results, 10)  # Max 10 per request
    }
    
    if search_type:
        params["searchType"] = search_type
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(GOOGLE_SEARCH_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse results
                    results = []
                    for item in data.get("items", []):
                        results.append({
                            "title": item.get("title", ""),
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": item.get("displayLink", "")
                        })
                    
                    return {
                        "success": True,
                        "query": query,
                        "total_results": data.get("searchInformation", {}).get("totalResults", "0"),
                        "results": results
                    }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "error": f"API Error {response.status}: {error_data.get('error', {}).get('message', 'Unknown error')}"
                    }
                    
    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }


async def web_search(query: str, num_results: int = 5) -> dict:
    """
    Unified web search - tries Google first, falls back to DuckDuckGo
    
    Args:
        query: Search query string
        num_results: Number of results
        
    Returns:
        dict with search results
    """
    # Try Google first
    google_result = await google_search(query, num_results)
    
    if google_result.get("success"):
        return google_result
    
    # Fallback to DuckDuckGo (free)
    print(f"Google Search failed: {google_result.get('error')}. Falling back to DuckDuckGo...")
    return await duckduckgo_search(query, num_results)


async def search_multiple_queries(queries: list[str], num_per_query: int = 3) -> dict:
    """
    Search multiple queries and combine results
    
    Args:
        queries: List of search queries
        num_per_query: Results per query
        
    Returns:
        Combined results from all queries
    """
    all_results = []
    
    for query in queries:
        result = await google_search(query, num_per_query)
        if result.get("success"):
            all_results.extend([
                {**r, "query": query} for r in result.get("results", [])
            ])
    
    return {
        "success": True,
        "total_queries": len(queries),
        "total_results": len(all_results),
        "results": all_results
    }


def format_search_results_for_agent(results: dict) -> str:
    """
    Format search results as text for agent consumption
    """
    if not results.get("success"):
        return f"Search Error: {results.get('error', 'Unknown error')}"
    
    output = f"WEB SEARCH RESULTS\n"
    output += f"==================\n"
    output += f"Total results found: {results.get('total_results', 'N/A')}\n\n"
    
    for i, result in enumerate(results.get("results", []), 1):
        output += f"[Result {i}]\n"
        output += f"Title: {result.get('title', 'N/A')}\n"
        output += f"Source: {result.get('source', 'N/A')}\n"
        output += f"URL: {result.get('link', 'N/A')}\n"
        output += f"Snippet: {result.get('snippet', 'N/A')}\n"
        output += f"\n"
    
    return output
