"""
CrawlConsole - Complete Firecrawl Clone Backend
================================================
5 Modes: Scrape, Search, Agent, Map, Crawl
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Windows Subprocess Support Fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from uuid import uuid4
from typing import Dict, Any, List, Optional, AsyncGenerator
from urllib.parse import urlparse, urljoin
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from bs4 import BeautifulSoup
import html2text

# ============================================
# WEB SCRAPER ENGINE
# ============================================

class WebScraper:
    """Core web scraping engine with Crawl4AI support"""
    
    def __init__(self):
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.body_width = 0
        self.crawler = None
    
    def set_crawler(self, crawler):
        self.crawler = crawler

    async def fetch_with_browser(self, url: str) -> Dict[str, Any]:
        """Fetch using Crawl4AI (JavaScript rendering)"""
        # Optimized: Use global warm crawler if available
        if self.crawler:
            try:
                # Use arun directly on the warm instance
                result = await self.crawler.arun(url=url, bypass_cache=True)
                if not result.success:
                    raise Exception(result.error_message or "Crawl failed")
                return {
                    "html": result.html,
                    "markdown": result.markdown,
                    "success": True
                }
            except Exception as e:
                return {"html": "", "markdown": "", "success": False, "error": str(e)}

        # Fallback: Create new instance (Slower)
        try:
            from crawl4ai import AsyncWebCrawler
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url, bypass_cache=True)
                if not result.success:
                    raise Exception(result.error_message or "Crawl failed")
                return {
                    "html": result.html,
                    "markdown": result.markdown,
                    "success": True
                }
        except Exception as e:
            return {"html": "", "markdown": "", "success": False, "error": str(e)}
    
    async def fetch_simple(self, url: str) -> Dict[str, Any]:
        """Simple HTTP fetch without browser"""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return {"html": response.text, "success": True, "status": response.status_code}
        except Exception as e:
            return {"html": "", "success": False, "error": str(e)}
    
    def html_to_markdown(self, html: str) -> str:
        """Convert HTML to clean Markdown"""
        return self.h2t.handle(html)
    
    def extract_text(self, html: str) -> str:
        """Extract plain text"""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(" ", strip=True)
    
    def extract_metadata(self, html: str, url: str) -> Dict:
        """Extract page metadata"""
        soup = BeautifulSoup(html, "html.parser")
        return {
            "title": soup.title.get_text(strip=True) if soup.title else "",
            "description": (soup.find("meta", {"name": "description"}) or {}).get("content", ""),
            "url": url,
            "fetched_at": datetime.utcnow().isoformat()
        }
    
    def extract_links(self, html: str, base_url: str) -> List[Dict]:
        """Extract all links"""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("mailto:", "javascript:", "#")):
                continue
            full_url = urljoin(base_url, href)
            if full_url not in seen:
                seen.add(full_url)
                links.append({
                    "url": full_url,
                    "text": a.get_text(strip=True)[:100],
                    "internal": urlparse(full_url).netloc == urlparse(base_url).netloc
                })
        return links
    
    def extract_images(self, html: str, base_url: str) -> List[Dict]:
        """Extract all images"""
        soup = BeautifulSoup(html, "html.parser")
        images = []
        for img in soup.find_all("img", src=True):
            src = urljoin(base_url, img["src"])
            images.append({
                "url": src,
                "alt": img.get("alt", "")
            })
        return images

scraper = WebScraper()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage global browser lifecycle for performance"""
    print("🚀 Starting CrawlConsole Engine...")
    try:
        from crawl4ai import AsyncWebCrawler
        # Initialize one global browser session
        async with AsyncWebCrawler(verbose=False) as crawler:
            scraper.set_crawler(crawler)
            yield
    except ImportError:
        print("⚠️ Crawl4AI not found, running in reduced mode.")
        yield
    finally:
        scraper.set_crawler(None)
        print("🛑 Engine stopped.")

# ============================================
# APP DEFINITION
# ============================================

app = FastAPI(
    title="CrawlConsole - Firecrawl Clone", 
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ============================================
# PYDANTIC MODELS
# ============================================

class ScrapeRequest(BaseModel):
    url: str
    format: str = "markdown"  # markdown, html, text
    include_links: bool = True
    include_images: bool = True
    use_browser: bool = True  # Use Crawl4AI for JS rendering

class SearchRequest(BaseModel):
    url: str
    query: str
    top_k: int = 10

class AgentRequest(BaseModel):
    url: str
    instruction: str
    model: str = "xiaomi/mimo-v2-flash:free"
    schema: Optional[Dict] = None

class MapRequest(BaseModel):
    url: str
    max_depth: int = 2
    max_pages: int = 50
    same_domain: bool = True

class CrawlRequest(BaseModel):
    urls: List[str]
    batch_size: int = 3
    format: str = "markdown"

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/scrape")
async def api_scrape(req: ScrapeRequest):
    """Scrape a single URL"""
    return await mode_scrape(req)

@app.post("/api/search")
async def api_search(req: SearchRequest):
    """Search content on a page"""
    return await mode_search(req)

@app.post("/api/agent")
async def api_agent(req: AgentRequest):
    """AI-powered extraction"""
    return await mode_agent(req)

@app.post("/api/map")
async def api_map(req: MapRequest):
    """Map site structure"""
    return await mode_map(req)

@app.post("/api/crawl")
async def api_crawl(req: CrawlRequest):
    """Batch crawl URLs"""
    return await mode_crawl(req)

@app.post("/api/crawl/stream")
async def api_crawl_stream(req: CrawlRequest):
    """Stream crawl results"""
    return StreamingResponse(
        mode_crawl_stream(req),
        media_type="application/x-ndjson"
    )

@app.get("/api/models")
async def get_models():
    """Available AI models"""
    return {
        "models": {
            "xiaomi/mimo-v2-flash:free": "Xiaomi MIMO v2 Flash (Free)",
            "mistralai/devstral-2512:free": "Mistral Devstral (Free)"
        }
    }

@app.get("/api/modes")
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

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# ============================================
# IMPLEMENTATION OF MODES
# ============================================

async def mode_scrape(req: ScrapeRequest) -> Dict:
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

async def mode_search(req: SearchRequest) -> Dict:
    from rank_bm25 import BM25Okapi
    
    result = await scraper.fetch_with_browser(req.url)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "mode": "search"}
    
    html = result["html"]
    soup = BeautifulSoup(html, "html.parser")
    
    paragraphs = []
    for tag in soup.find_all(["p", "li", "h1", "h2", "h3", "td"]):
        text = tag.get_text(strip=True)
        if len(text) > 20:
            paragraphs.append(text)
    
    if not paragraphs:
        paragraphs = [soup.get_text(strip=True)]
    
    tokenized = [p.lower().split() for p in paragraphs]
    bm25 = BM25Okapi(tokenized)
    query_tokens = req.query.lower().split()
    scores = bm25.get_scores(query_tokens)
    
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

async def mode_agent(req: AgentRequest) -> Dict:
    result = await scraper.fetch_with_browser(req.url)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "mode": "agent"}
    
    content = result.get("markdown") or scraper.extract_text(result["html"])
    content = content[:8000]
    
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return {
            "success": False,
            "mode": "agent",
            "error": "OPENROUTER_API_KEY not set. Set it to use AI extraction.",
            "url": req.url
        }
    
    try:
        from pydantic_ai import Agent
        from pydantic_ai.providers.openai import OpenAIProvider
        
        provider = OpenAIProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        agent = Agent(
            req.model,
            provider=provider,
            instructions="You are a data extraction agent. Follow the user's instructions precisely."
        )
        
        prompt = f"""Instruction: {req.instruction}

Content from {req.url}:
{content}

Extract the requested information and respond in JSON format."""
        
        ai_result = await agent.run(prompt)
        
        return {
            "success": True,
            "mode": "agent",
            "url": req.url,
            "instruction": req.instruction,
            "model": req.model,
            "extracted": ai_result.output
        }
    except Exception as e:
        return {
            "success": False,
            "mode": "agent",
            "url": req.url,
            "error": str(e)
        }

async def mode_map(req: MapRequest) -> Dict:
    visited = set()
    site_map = []
    queue = [(req.url, 0)]
    base_domain = urlparse(req.url).netloc
    
    while queue and len(visited) < req.max_pages:
        current_url, depth = queue.pop(0)
        
        if current_url in visited or depth > req.max_depth:
            continue
        
        visited.add(current_url)
        
        try:
            result = await scraper.fetch_simple(current_url)
            if not result.get("success"):
                site_map.append({
                    "url": current_url,
                    "depth": depth,
                    "error": result.get("error"),
                    "links": []
                })
                continue
            
            html = result["html"]
            metadata = scraper.extract_metadata(html, current_url)
            links = scraper.extract_links(html, current_url)
            
            site_map.append({
                "url": current_url,
                "depth": depth,
                "title": metadata["title"],
                "links_count": len(links)
            })
            
            for link in links:
                if link["internal"] and link["url"] not in visited:
                    if req.same_domain and urlparse(link["url"]).netloc == base_domain:
                        queue.append((link["url"], depth + 1))
        
        except Exception as e:
            site_map.append({
                "url": current_url,
                "depth": depth,
                "error": str(e)
            })
    
    return {
        "success": True,
        "mode": "map",
        "root_url": req.url,
        "pages_discovered": len(visited),
        "max_depth": req.max_depth,
        "site_map": site_map
    }

async def mode_crawl(req: CrawlRequest) -> Dict:
    semaphore = asyncio.Semaphore(req.batch_size)
    results = []
    
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
