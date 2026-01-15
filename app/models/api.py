from pydantic import BaseModel
from typing import List, Dict, Optional

class ScrapeRequest(BaseModel):
    url: str
    format: str = "markdown"  # markdown, html, text
    include_links: bool = True
    include_images: bool = True
    use_browser: bool = True  # Use Crawl4AI for JS rendering

class SearchRequest(BaseModel):
    url: str
    query: str
    top_k: int = 10

class AgentRequest(BaseModel):
    url: str
    instruction: str
    model: str = "xiaomi/mimo-v2-flash:free"
    schema: Optional[Dict] = None

class MapRequest(BaseModel):
    url: str
    max_depth: int = 2
    max_pages: int = 50
    same_domain: bool = True

class CrawlRequest(BaseModel):
    urls: List[str]
    batch_size: int = 3
    format: str = "markdown"
