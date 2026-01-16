
import asyncio
import sys

def new_event_loop():
    """
    Custom event loop factory for Uvicorn.
    Ensures WindowsProactorEventLoopPolicy is set before creating the loop.
    This is critical for Playwright/Crawl4AI support on Windows during hot reload.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.new_event_loop()
