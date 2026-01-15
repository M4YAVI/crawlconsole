
import uvicorn
import sys
import asyncio
import os

if __name__ == "__main__":
    # FORCE Windows Proactor Event Loop for Subprocess Support (Playwright/Crawl4AI)
    if sys.platform == "win32":
        print("🔧 Configuring Windows Event Loop Policy...")
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run Uvicorn
    print("🚀 Starting CrawlConsole Server...")
    uvicorn.run(
        "app.main:app", 
        host="127.0.0.1", 
        port=8001, 
        reload=False,
        loop="asyncio"  # Explicitly request asyncio loop
    )
