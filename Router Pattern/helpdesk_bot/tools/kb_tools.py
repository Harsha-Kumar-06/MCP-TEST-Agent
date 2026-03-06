"""
Knowledge Base Tools - RAG Implementation with Vector Search.

Uses ChromaDB for vector storage and Gemini for embeddings.

Knowledge Base can be loaded from:
- In-code sample data (default)
- JSON file (data/knowledge_base.json)
- CSV file (data/knowledge_base.csv)

Configure via .env: KB_SOURCE=json and KB_JSON_PATH=data/knowledge_base.json
"""

import os
import json
import csv
from typing import Optional, List
from datetime import datetime

from dotenv import load_dotenv

# Use the new google.genai package
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    genai = None

load_dotenv()

# ============================================================
# KB CONFIGURATION
# ============================================================
# Source options: static, json, csv
KB_SOURCE = os.getenv("KB_SOURCE", "static")
KB_JSON_PATH = os.getenv("KB_JSON_PATH", "data/knowledge_base.json")
KB_CSV_PATH = os.getenv("KB_CSV_PATH", "data/knowledge_base.csv")

# ============================================================
# KB LOADER FUNCTIONS
# ============================================================

def load_kb_from_json(file_path: str = None) -> List[dict]:
    """
    Load knowledge base articles from a JSON file.
    
    Expected JSON format:
    [
        {
            "id": "article_id",
            "title": "Article Title",
            "content": "Full article content...",
            "category": "IT_Support",
            "tags": ["tag1", "tag2"]
        }
    ]
    """
    file_path = file_path or KB_JSON_PATH
    
    try:
        # Handle relative paths
        if not os.path.isabs(file_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            full_path = os.path.join(project_root, file_path)
            if not os.path.exists(full_path):
                full_path = file_path
        else:
            full_path = file_path
        
        with open(full_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        print(f"Loaded {len(articles)} KB articles from JSON: {full_path}")
        return articles
    
    except FileNotFoundError:
        print(f"KB JSON file not found: {file_path}, using sample data")
        return None
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in KB file: {e}")
        return None


def load_kb_from_csv(file_path: str = None) -> List[dict]:
    """
    Load knowledge base articles from a CSV file.
    
    Expected CSV format:
    id,title,content,category,tags
    password_reset,"Password Reset Guide","Full content...",IT_Support,"password,login,access"
    """
    file_path = file_path or KB_CSV_PATH
    articles = []
    
    try:
        # Handle relative paths
        if not os.path.isabs(file_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            full_path = os.path.join(project_root, file_path)
            if not os.path.exists(full_path):
                full_path = file_path
        else:
            full_path = file_path
        
        with open(full_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tags_str = row.get('tags', '')
                tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                
                articles.append({
                    "id": row.get('id', '').strip(),
                    "title": row.get('title', '').strip(),
                    "content": row.get('content', '').strip(),
                    "category": row.get('category', '').strip(),
                    "tags": tags
                })
        
        print(f"Loaded {len(articles)} KB articles from CSV: {full_path}")
        return articles
    
    except FileNotFoundError:
        print(f"KB CSV file not found: {file_path}, using sample data")
        return None


def get_kb_documents() -> List[dict]:
    """
    Get KB documents from the configured source.
    """
    source = KB_SOURCE.lower()
    
    if source == "json":
        articles = load_kb_from_json()
        if articles:
            return articles
    
    elif source == "csv":
        articles = load_kb_from_csv()
        if articles:
            return articles
    
    # Default to sample data
    return SAMPLE_KB_DOCUMENTS

# ============================================================
# SAMPLE KB DATA (Replace with your actual KB content)
# ============================================================

SAMPLE_KB_DOCUMENTS = [
    {
        "id": "password_reset",
        "title": "How to Reset Your Password",
        "content": """To reset your password:
1. Go to https://password.company.com
2. Click 'Forgot Password'
3. Enter your employee email
4. Check your email for reset link
5. Create a new password (min 12 chars, 1 uppercase, 1 number, 1 special)

If you're locked out, contact IT Support at ext. 4357.""",
        "category": "IT_Support",
        "tags": ["password", "login", "access", "locked out", "forgot password"]
    },
    {
        "id": "pto_policy",
        "title": "PTO Policy Overview", 
        "content": """Annual PTO Allocation:
- 0-2 years: 15 days
- 3-5 years: 20 days
- 6+ years: 25 days

Requesting PTO:
1. Submit via Workday at least 2 weeks in advance
2. Manager approval required
3. Blackout dates: Dec 20-Jan 2, Q4 close period

Carryover: Max 5 days to next year. Use it or lose it!""",
        "category": "HR",
        "tags": ["pto", "vacation", "time off", "leave", "days off"]
    },
    {
        "id": "vpn_setup",
        "title": "VPN Setup Guide",
        "content": """Setting up VPN:
1. Download GlobalProtect from software.company.com
2. Install and launch the application
3. Enter portal: vpn.company.com
4. Login with your AD credentials
5. Click 'Connect'

Troubleshooting:
- If connection fails, check your internet first
- Clear credentials and re-enter
- Restart the VPN client
- Contact IT if issues persist""",
        "category": "IT_Support",
        "tags": ["vpn", "remote", "connect", "work from home", "globalprotect"]
    },
    {
        "id": "expense_policy",
        "title": "Expense Reimbursement Policy",
        "content": """Submitting Expenses:
1. Use Concur at expenses.company.com
2. Upload receipts within 30 days
3. Categorize correctly (Travel, Meals, Supplies, etc.)

Limits:
- Meals: $50/day domestic, $75/day international
- Hotels: Use corporate rate or $200/night max
- Flights: Economy class, book 14+ days ahead

Manager approval required for expenses > $500.""",
        "category": "HR",
        "tags": ["expense", "reimbursement", "receipt", "travel", "concur"]
    },
    {
        "id": "laptop_slow",
        "title": "Fixing a Slow Laptop",
        "content": """Quick fixes for slow performance:
1. Restart your laptop (seriously, it helps!)
2. Close unused browser tabs and applications
3. Run Disk Cleanup: Search 'Disk Cleanup' in Start
4. Check for Windows updates
5. Clear browser cache

If still slow after these steps:
- Check Task Manager for high CPU/memory usage
- Run antivirus scan
- Submit IT ticket for hardware diagnostics""",
        "category": "IT_Support",
        "tags": ["slow", "performance", "laptop", "computer", "speed"]
    },
    {
        "id": "benefits_enrollment",
        "title": "Benefits Enrollment Guide",
        "content": """Open Enrollment: November 1-15 each year

Available Benefits:
- Medical: PPO, HMO, HDHP options
- Dental: Basic and Premium plans
- Vision: VSP coverage
- 401k: Company matches up to 6%
- Life Insurance: 1x salary free, additional available

How to Enroll:
1. Login to Workday
2. Go to Benefits > Change Benefits
3. Review and select plans
4. Add dependents if needed
5. Confirm selections before deadline""",
        "category": "HR",
        "tags": ["benefits", "health", "insurance", "401k", "enrollment", "medical", "dental"]
    },
    {
        "id": "software_request",
        "title": "How to Request Software",
        "content": """To request new software:
1. Go to ServiceNow portal: service.company.com
2. Click 'Request Software'
3. Search for the software you need
4. Fill out business justification
5. Submit for approval

Approval timeline:
- Free software: 1-2 business days
- Paid software: 3-5 business days (requires manager + budget approval)
- Enterprise software: 1-2 weeks (requires director approval)

For urgent requests, contact IT directly.""",
        "category": "IT_Support",
        "tags": ["software", "install", "application", "license", "request"]
    },
    {
        "id": "onboarding_checklist",
        "title": "New Employee Onboarding Checklist",
        "content": """Welcome! Complete these in your first week:

Day 1:
- Pick up laptop from IT (Room 101)
- Complete I-9 verification with HR
- Set up email and Slack

Week 1:
- Complete security training (mandatory)
- Set up direct deposit in Workday
- Enroll in benefits
- Meet with your manager for 30/60/90 plan
- Join team channels in Slack

Resources:
- IT Help: ext. 4357
- HR Help: ext. 4200
- Facilities: ext. 4100""",
        "category": "HR",
        "tags": ["onboarding", "new hire", "first day", "setup", "checklist"]
    }
]

# ============================================================
# RAG Implementation with ChromaDB
# ============================================================

_chroma_collection = None
_genai_client = None


def _get_genai_client():
    """Get or create Gemini client."""
    global _genai_client
    if _genai_client is None and HAS_GENAI:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            _genai_client = genai.Client(api_key=api_key)
    return _genai_client


def _get_chroma_collection():
    """Get or create the ChromaDB collection with embeddings."""
    global _chroma_collection
    
    if _chroma_collection is not None:
        return _chroma_collection
    
    try:
        import chromadb
        
        # Initialize ChromaDB client (in-memory for simplicity)
        chroma_client = chromadb.Client()
        
        # Create or get collection
        collection = chroma_client.get_or_create_collection(
            name="helpdesk_kb",
            metadata={"description": "HelpDesk Knowledge Base"}
        )
        
        # Check if we need to populate the collection
        if collection.count() == 0:
            print("Initializing KB vector store...")
            _populate_collection(collection)
        
        _chroma_collection = collection
        return collection
        
    except ImportError:
        print("ChromaDB not installed. Using keyword search. Run: pip install chromadb")
        return None
    except Exception as e:
        print(f"Error initializing ChromaDB: {e}")
        return None


def _populate_collection(collection):
    """Populate ChromaDB with KB documents and embeddings."""
    documents = []
    metadatas = []
    ids = []
    embeddings = []
    
    kb_docs = get_kb_documents()
    for doc in kb_docs:
        # Combine title and content for embedding
        full_text = f"{doc['title']}\n\n{doc['content']}"
        documents.append(full_text)
        metadatas.append({
            "title": doc["title"],
            "category": doc["category"],
            "tags": ",".join(doc["tags"]),
            "id": doc["id"]
        })
        ids.append(doc["id"])
        
        # Generate embedding using Gemini
        embedding = _get_embedding(full_text)
        if embedding:
            embeddings.append(embedding)
    
    # Add to collection
    if embeddings and len(embeddings) == len(documents):
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )
        print(f"Added {len(documents)} documents to KB vector store with embeddings")
    else:
        # Add without embeddings (ChromaDB will use default)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(documents)} documents to KB vector store (default embeddings)")


def _get_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list:
    """Generate embedding for text using Gemini."""
    client = _get_genai_client()
    if not client:
        return None
    
    try:
        # Use gemini-embedding-001 which is the current supported model
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(task_type=task_type)
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"Embedding error: {e}")
        return None


def search_knowledge_base(
    query: str,
    category: str,
    max_results: int
) -> dict:
    """
    Search the knowledge base using semantic vector search (RAG).
    
    Args:
        query: Natural language search query
        category: Category filter (IT_Support, HR, Sales, Legal) - use empty string for all
        max_results: Maximum number of results to return (recommended: 3)
    
    Returns:
        dict: Search results with relevant KB articles
    """
    collection = _get_chroma_collection()
    
    if collection is None:
        # Fallback to keyword search if ChromaDB unavailable
        return _keyword_search(query, category, max_results)
    
    try:
        # Build where filter for category
        where_filter = None
        if category:
            where_filter = {"category": category}
        
        # Try semantic search with query embedding
        query_embedding = _get_embedding(query, task_type="RETRIEVAL_QUERY")
        
        if query_embedding:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                where=where_filter
            )
            search_method = "semantic_vector_search"
        else:
            # Fallback to text-based query
            results = collection.query(
                query_texts=[query],
                n_results=max_results,
                where=where_filter
            )
            search_method = "text_search"
        
        # Format results
        formatted_results = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results.get("distances") else 0
                
                formatted_results.append({
                    "article_id": metadata.get("id", f"doc_{i}"),
                    "title": metadata.get("title", "Untitled"),
                    "content": doc,
                    "category": metadata.get("category", "General"),
                    "relevance_score": round(1 - distance, 3) if distance else 0.5,
                    "tags": metadata.get("tags", "").split(",")
                })
        
        return {
            "query": query,
            "search_method": search_method,
            "total_results": len(formatted_results),
            "results": formatted_results,
            "search_tip": "Results ranked by semantic similarity to your question."
        }
        
    except Exception as e:
        print(f"Vector search error: {e}")
        return _keyword_search(query, category, max_results)


def _keyword_search(query: str, category: str, max_results: int) -> dict:
    """Fallback keyword search when vector search unavailable."""
    query_lower = query.lower()
    results = []
    
    kb_docs = get_kb_documents()
    for doc in kb_docs:
        if category and doc["category"] != category:
            continue
        
        # Calculate relevance score
        score = 0
        searchable = f"{doc['title']} {doc['content']} {' '.join(doc['tags'])}".lower()
        
        for word in query_lower.split():
            if len(word) > 2 and word in searchable:
                score += searchable.count(word)
        
        if score > 0:
            results.append({
                "article_id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "category": doc["category"],
                "relevance_score": score,
                "tags": doc["tags"]
            })
    
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return {
        "query": query,
        "search_method": "keyword_search",
        "total_results": len(results),
        "results": results[:max_results],
        "search_tip": "Using keyword search. Install chromadb for better semantic search."
    }


def get_kb_article(article_id: str) -> dict:
    """
    Retrieve a specific KB article by ID.
    
    Args:
        article_id: The unique identifier of the KB article
    
    Returns:
        dict: The full article content
    """
    kb_docs = get_kb_documents()
    for doc in kb_docs:
        if doc["id"] == article_id:
            return {
                "found": True,
                "article_id": article_id,
                "title": doc["title"],
                "content": doc["content"],
                "category": doc["category"],
                "tags": doc["tags"],
                "related_articles": _find_related(article_id)
            }
    
    return {
        "found": False,
        "error": f"Article '{article_id}' not found",
        "suggestion": "Try searching the knowledge base instead"
    }


def _find_related(article_id: str) -> list:
    """Find related articles based on category and tags."""
    kb_docs = get_kb_documents()
    current = next((d for d in kb_docs if d["id"] == article_id), None)
    if not current:
        return []
    
    related = []
    for doc in kb_docs:
        if doc["id"] == article_id:
            continue
        if doc["category"] == current["category"]:
            related.append({"id": doc["id"], "title": doc["title"]})
    
    return related[:3]
