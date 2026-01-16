"""
API Request/Response Models
"""
from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class ScrapeRequest(BaseModel):
    """Scrape request model"""
    url: str
    format: str = "markdown"  # "markdown", "text", "html"
    use_browser: bool = False
    include_links: bool = False
    include_images: bool = False

class CrawlRequest(BaseModel):
    """Crawl request model for batch processing"""
    urls: List[str]
    format: str = "markdown"
    batch_size: int = 5
    use_browser: bool = False
    include_links: bool = False
    include_images: bool = False

class MapRequest(BaseModel):
    """Map request model"""
    url: str
    max_pages: int = 50
    max_depth: int = 2
    same_domain: bool = True

class SearchRequest(BaseModel):
    """Search request model"""
    url: str
    query: str
    top_k: int = 5

class AgentRequest(BaseModel):
    """Agent request model"""
    url: str
    instruction: str
    model: Optional[str] = "anthropic/claude-3.5-sonnet"
