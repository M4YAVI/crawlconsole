"""
Scrape Feature Service
"""
import logging
from typing import Dict, Any
from ...models.api import ScrapeRequest
from ...services.scraper import scraper

logger = logging.getLogger(__name__)

async def mode_scrape(req: ScrapeRequest) -> Dict[str, Any]:
    """
    SCRAPE MODE: Extract clean content from a single URL
    - Supports Markdown, HTML, and Text formats
    - Optional link and image extraction
    """
    try:
        logger.info(f"Scraping URL: {req.url}, format: {req.format}, browser: {req.use_browser}")
        
        # Fetch HTML from URL
        if req.use_browser:
            result = await scraper.fetch_with_browser(req.url)
        else:
            result = await scraper.fetch_simple(req.url)
        
        # Check if fetch was successful
        if not result.get("success"):
            error_msg = result.get("error", "Fetch failed")
            logger.error(f"Fetch failed for {req.url}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "url": req.url,
                "mode": "scrape"
            }
        
        html = result.get("html", "")
        if not html:
            logger.warning(f"Empty HTML returned for {req.url}")
            return {
                "success": False,
                "error": "Empty HTML response",
                "url": req.url,
                "mode": "scrape"
            }
        
        # Extract metadata
        try:
            metadata = scraper.extract_metadata(html, req.url)
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            metadata = {"title": "", "description": "", "author": "", "keywords": "", "favicon": "", "url": req.url}
        
        # Format content based on user request
        content = ""
        if req.format == "markdown":
            content = result.get("markdown")
            # If markdown wasn't pre-generated (e.g. simple fetch) or if we need to regenerate with specific options
            # Note: Browser fetch usually returns markdown, but simple fetch does it too.
            # However, the initial fetch doesn't know about user options in the current implementation.
            # So we should RE-RUN html_to_markdown here with the correct options using the raw HTML.
            content = scraper.html_to_markdown(html, include_links=req.include_links, include_images=req.include_images)
        elif req.format == "text":
            content = scraper.extract_text(html)
        else:  # html
            content = html
        
        # Build base response
        response = {
            "success": True,
            "mode": "scrape",
            "url": req.url,
            "metadata": metadata,
            "content": content,  # No limit
            "format": req.format
        }
        
        # Fixed: Only add links if explicitly selected
        if req.include_links is True:
            try:
                response["links"] = scraper.extract_links(html, req.url)
                logger.info(f"Extracted {len(response['links'])} links")
            except Exception as e:
                logger.warning(f"Failed to extract links: {e}")
                response["links"] = []
        
        # Fixed: Only add images if explicitly selected
        if req.include_images is True:
            try:
                response["images"] = scraper.extract_images(html, req.url)
                logger.info(f"Extracted {len(response['images'])} images")
            except Exception as e:
                logger.warning(f"Failed to extract images: {e}")
                response["images"] = []
        
        logger.info(f"Successfully scraped {req.url}")
        return response
    
    except Exception as e:
        logger.error(f"Unexpected error in mode_scrape: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "mode": "scrape"
        }
