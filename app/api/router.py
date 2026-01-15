import asyncio
import json
import os
from typing import Dict, Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models.api import (
    ScrapeRequest, SearchRequest, AgentRequest, MapRequest, CrawlRequest
)
from ..services.crawler import scraper
from ..services.search import mode_search
from ..services.ai import mode_agent
from ..services.map import mode_map

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/modes")
async def get_modes():
    """List available modes"""
    return {
        "modes": [
            {"name": "scrape", "description": "Extract clean markdown from any URL", "icon": "📄"},
            {"name": "search", "description": "Find content matching a query", "icon": "🔍"},
            {"name": "agent", "description": "AI-powered data extraction", "icon": "🤖"},
            {"name": "map", "description": "Map entire site structure", "icon": "🗺️"},
            {"name": "crawl", "description": "Batch crawl multiple URLs", "icon": "🕷️"}
        ]
    }

@router.get("/models")
async def get_models():
    """Available AI models"""
    return {
        "models": {
            "xiaomi/mimo-v2-flash:free": "Xiaomi MIMO v2 Flash (Free)",
            "mistralai/devstral-2512:free": "Mistral Devstral (Free)"
        }
    }

@router.post("/scrape")
async def api_scrape(req: ScrapeRequest):
    """Scrape a single URL"""
    if req.use_browser:
        result = await scraper.fetch_with_browser(req.url)
    else:
        result = await scraper.fetch_simple(req.url)
    
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Fetch failed"), "mode": "scrape"}
    
    html = result["html"]
    metadata = scraper.extract_metadata(html, req.url)
    
    if req.format == "markdown":
        content = result.get("markdown") or scraper.html_to_markdown(html)
    elif req.format == "text":
        content = scraper.extract_text(html)
    else:
        content = html
    
    response = {
        "success": True,
        "mode": "scrape",
        "url": req.url,
        "metadata": metadata,
        "content": content,
        "format": req.format
    }
    
    if req.include_links:
        response["links"] = scraper.extract_links(html, req.url)
    if req.include_images:
        response["images"] = scraper.extract_images(html, req.url)
    
    return response

@router.post("/search")
async def api_search(req: SearchRequest):
    """Search content on a page"""
    return await mode_search(req)

@router.post("/agent")
async def api_agent(req: AgentRequest):
    """AI-powered extraction"""
    return await mode_agent(req)

@router.post("/map")
async def api_map(req: MapRequest):
    """Map site structure"""
    return await mode_map(req)

@router.post("/crawl")
async def api_crawl(req: CrawlRequest):
    """Batch crawl URLs"""
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

@router.post("/crawl/stream")
async def api_crawl_stream(req: CrawlRequest):
    """Stream crawl results"""
    semaphore = asyncio.Semaphore(req.batch_size)
    
    async def crawl_stream_generator():
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

    return StreamingResponse(
        crawl_stream_generator(),
        media_type="application/x-ndjson"
    )
