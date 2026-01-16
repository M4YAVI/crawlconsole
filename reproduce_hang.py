import asyncio
from app.services.scraper import scraper
from app.models.api import ScrapeRequest

async def test_scrape():
    print("Starting test scrape...")
    
    # Test Browser Fetch
    print("\n--- Testing Browser Fetch ---")
    req_browser = ScrapeRequest(
        url="https://example.com",
        format="markdown",
        include_links=True,
        include_images=True,
        use_browser=True
    )
    
    print("Calling fetch_with_browser...")
    try:
        # This will spin up a new AsyncWebCrawler instance since global is not set
        result = await scraper.fetch_with_browser(req_browser.url)
        print(f"Browser fetch success: {result.get('success')}")
        if not result.get("success"):
            print(f"Error: {result.get('error')}")
        else:
            print("Browser fetch completed.")
            html = result["html"]
            if req_browser.include_links is True:
                links = scraper.extract_links(html, req_browser.url)
                print(f"Links extracted: {len(links)}")
    except Exception as e:
        print(f"Exception during browser fetch: {e}")
    finally:
        # Checking if cleanup method exists and calling it mostly for global scraper
        if hasattr(scraper, 'cleanup'):
            print("Cleaning up...")
            await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(test_scrape())
