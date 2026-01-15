import asyncio
import json
from typing import Dict, Any, AsyncGenerator
from ..models.api import CrawlRequest
from .crawler import scraper

async def mode_crawl(req: CrawlRequest) -> Dict[str, Any]:
    """
    CRAWL MODE: Batch crawl multiple URLs in parallel
    - Semaphore-controlled concurrency
    - Returns consolidated results
    """
    semaphore = asyncio.Semaphore(req.batch_size)
    
    async def crawl_one(url: str) -> Dict:
        async with semaphore:
            try:
                data = await scraper.fetch_with_browser(url)
                if not data.get("success"):
                    return {"url": url, "success": False, "error": data.get("error")}
                
                html = data["html"]
                if req.format == "markdown":
                    content = data.get("markdown") or scraper.html_to_markdown(html)
                elif req.format == "text":
                    content = scraper.extract_text(html)
                else:
                    content = html
                
                return {
                    "url": url,
                    "success": True,
                    "metadata": scraper.extract_metadata(html, url),
                    "content": content[:5000]
                }
            except Exception as e:
                return {"url": url, "success": False, "error": str(e)}
    
    tasks = [crawl_one(url) for url in req.urls]
    results = await asyncio.gather(*tasks)
    
    successful = sum(1 for r in results if r.get("success"))
    
    return {
        "success": True,
        "mode": "crawl",
        "total_urls": len(req.urls),
        "successful": successful,
        "failed": len(req.urls) - successful,
        "results": results
    }

async def mode_crawl_stream(req: CrawlRequest) -> AsyncGenerator[str, None]:
    """
    CRAWL STREAM: Batch crawl with real-time feedback
    - Yields results as they are completed
    - NDJSON format
    """
    semaphore = asyncio.Semaphore(req.batch_size)
    
    async def crawl_one(url: str) -> Dict:
        async with semaphore:
            try:
                data = await scraper.fetch_with_browser(url)
                if not data.get("success"):
                    return {"url": url, "success": False, "error": data.get("error")}
                
                content = data.get("markdown") or scraper.html_to_markdown(data["html"])
                return {"url": url, "success": True, "content": content[:3000]}
            except Exception as e:
                return {"url": url, "success": False, "error": str(e)}
    
    for url in req.urls:
        result = await crawl_one(url)
        yield json.dumps(result) + "\n"
