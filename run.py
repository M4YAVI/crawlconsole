
import uvicorn
import sys
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from parent directory (firecrawl-clone/.env)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    print(f"✅ Loading environment from: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print("⚠️  Warning: .env file not found in parent directory")
    # Try current directory as fallback
    load_dotenv()

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
        port=8000, 
        reload=True,
        loop="app.loop_setup:new_event_loop"  # Use custom loop factory for Windows support
    )
