"""
CrawlConsole - Complete Firecrawl Clone (Refactored)
====================================================
Modular Architecture:
- app/api: Route handlers
- app/services: Business logic
- app/models: Pydantic schemas
"""

import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Windows Subprocess Support Fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from .services.crawler import scraper
from .api.router import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage global browser lifecycle"""
    print("🚀 Starting CrawlConsole Engine...")
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler(verbose=False) as crawler:
            scraper.set_crawler(crawler)
            yield
    except ImportError:
        print("⚠️ Crawl4AI not found, running in reduced mode.")
        yield
    finally:
        scraper.set_crawler(None)
        print("🛑 Engine stopped.")

# App Initialization
app = FastAPI(
    title="CrawlConsole",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API Router
app.include_router(router, prefix="/api")

# Root Route
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return f.read()
