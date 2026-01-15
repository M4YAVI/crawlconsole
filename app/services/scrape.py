from typing import Dict, Any
from ..models.api import ScrapeRequest
from .crawler import scraper

async def mode_scrape(req: ScrapeRequest) -> Dict[str, Any]:
    """
    SCRAPE MODE: Extract clean content from a single URL
    - Supports Markdown, HTML, and Text formats
    - Optional link and image extraction
    """
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
