"""
Search Feature Service
"""
from bs4 import BeautifulSoup
from rank_bm25 import BM25Okapi
from typing import Dict, Any
from ...models.api import SearchRequest
from ...services.scraper import scraper

async def mode_search(req: SearchRequest) -> Dict[str, Any]:
    """
    SEARCH MODE: Find content matching a query
    - BM25 ranking algorithm
    - Returns top-k relevant chunks
    """
    result = await scraper.fetch_with_browser(req.url)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "mode": "search"}
    
    html = result["html"]
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract paragraphs
    paragraphs = []
    for tag in soup.find_all(["p", "li", "h1", "h2", "h3", "td"]):
        text = tag.get_text(strip=True)
        if len(text) > 20:
            paragraphs.append(text)
    
    if not paragraphs:
        paragraphs = [soup.get_text(strip=True)]
    
    # BM25 ranking
    tokenized = [p.lower().split() for p in paragraphs]
    bm25 = BM25Okapi(tokenized)
    query_tokens = req.query.lower().split()
    scores = bm25.get_scores(query_tokens)
    
    # Get top results
    ranked = sorted(zip(paragraphs, scores), key=lambda x: x[1], reverse=True)
    
    return {
        "success": True,
        "mode": "search",
        "url": req.url,
        "query": req.query,
        "results": [
            {"text": text, "score": round(float(score), 4)}
            for text, score in ranked[:req.top_k] if score > 0
        ],
        "total_paragraphs": len(paragraphs)
    }
