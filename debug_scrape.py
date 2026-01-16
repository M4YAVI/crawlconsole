import asyncio
import traceback
from app.services.scraper import scraper

async def debug_scrape():
    url = "https://www.anthropic.com/news/claude-haiku-4-5"
    print(f"--- Debugging Scrape for {url} ---")
    
    print("\n1. Testing Simple Fetch...")
    try:
        result = await scraper.fetch_simple(url)
        print(f"Result: {result['success']}")
        if not result['success']:
            print(f"Error: '{result.get('error')}'")
    except Exception:
        traceback.print_exc()

    print("\n2. Testing Browser Fetch...")
    try:
        result = await scraper.fetch_with_browser(url)
        print(f"Result: {result['success']}")
        if not result['success']:
            print(f"Error: '{result.get('error')}'")
    except Exception:
        traceback.print_exc()

    await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_scrape())
