"""
Crawl Feature Service
"""
import asyncio
import json
import logging
from typing import Dict, Any, AsyncGenerator

from ...models.api import CrawlRequest
from ...services.scraper import scraper

logger = logging.getLogger(__name__)

async def mode_crawl(req: CrawlRequest) -> Dict[str, Any]:
    """
    CRAWL MODE: Batch crawl multiple URLs in parallel
    - Semaphore-controlled concurrency
    - Returns consolidated results
    """
    semaphore = asyncio.Semaphore(req.batch_size)
    logger.info(f"Starting crawl of {len(req.urls)} URLs with batch size {req.batch_size}")
    
    async def crawl_one(url: str) -> Dict:
        async with semaphore:
            try:
                if req.use_browser:
                    data = await scraper.fetch_with_browser(url)
                else:
                    data = await scraper.fetch_simple(url)
                
                if not data.get("success"):
                    return {"url": url, "success": False, "error": data.get("error")}
                
                html = data["html"]
                metadata = scraper.extract_metadata(html, url)
                
                # Format content
                if req.format == "markdown":
                    content = data.get("markdown") or scraper.html_to_markdown(html)
                elif req.format == "text":
                    content = scraper.extract_text(html)
                else:
                    content = html
                
                result = {
                    "url": url,
                    "success": True,
                    "metadata": metadata,
                    "content": content[:5000]
                }
                
                # Optional: Add links/images
                if req.include_links is True:
                    result["links"] = scraper.extract_links(html, url)
                
                if req.include_images is True:
                    result["images"] = scraper.extract_images(html, url)
                
                return result
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                return {"url": url, "success": False, "error": str(e)}
    
    tasks = [crawl_one(url) for url in req.urls]
    results = await asyncio.gather(*tasks)
    
    successful = sum(1 for r in results if r.get("success"))
    
    logger.info(f"Crawl completed: {successful}/{len(req.urls)} successful")
    
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
    logger.info(f"Starting streaming crawl of {len(req.urls)} URLs")
    
    async def crawl_one(url: str) -> Dict:
        async with semaphore:
            try:
                if req.use_browser:
                    data = await scraper.fetch_with_browser(url)
                else:
                    data = await scraper.fetch_simple(url)
                
                if not data.get("success"):
                    return {"url": url, "success": False, "error": data.get("error")}
                
                html = data["html"]
                
                # Format content
                if req.format == "markdown":
                    content = data.get("markdown") or scraper.html_to_markdown(html)
                elif req.format == "text":
                    content = scraper.extract_text(html)
                else:
                    content = html
                
                result = {"url": url, "success": True, "content": content[:3000]}
                
                # Optional: Add links/images
                if req.include_links is True:
                    result["links"] = scraper.extract_links(html, url)
                
                if req.include_images is True:
                    result["images"] = scraper.extract_images(html, url)
                
                return result
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                return {"url": url, "success": False, "error": str(e)}
    
    for url in req.urls:
        result = await crawl_one(url)
        yield json.dumps(result) + "\n"
