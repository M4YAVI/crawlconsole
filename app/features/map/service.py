"""
Map Feature Service
"""
from urllib.parse import urlparse
from typing import Dict, Any
from ...models.api import MapRequest
from ...services.scraper import scraper

async def mode_map(req: MapRequest) -> Dict[str, Any]:
    """
    MAP MODE: Deep crawl and map site structure
    - BFS traversal
    - Respects depth/page limits
    - Returns site hierarchy
    """
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
            
            # Add internal links to queue
            for link in links:
                # Basic check for internal links
                if urlparse(link["url"]).netloc == base_domain:
                     if link["url"] not in visited:
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
