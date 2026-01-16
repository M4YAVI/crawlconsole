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

# Windows Subprocess Support & Event Loop Fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # SILENCE THE NOISY "Event loop is closed" ERROR ON WINDOWS
    from functools import wraps
    from asyncio.proactor_events import _ProactorBasePipeTransport

    def silence_event_loop_closed(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except RuntimeError as e:
                if str(e) != 'Event loop is closed':
                    raise
        return wrapper

    _ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)

from .services.scraper import scraper
from .api.router import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage global browser lifecycle"""
    print("🚀 Starting CrawlConsole Engine...")
    try:
        # Background eager loading: Start warmup immediately but don't await execution
        # asyncio.create_task(scraper.warmup()) # Playwright doesn't need explicit warmup generally, but we can if we want to launch browser early
        # For simplicity, we just yield as the new scraper is on-demand
        await scraper.startup()
        yield
    finally:
        await scraper.cleanup()
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
