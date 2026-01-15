import html2text
from typing import Dict, Any, List
from urllib.parse import urlparse, urljoin
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

class WebScraper:
    """Core web scraping engine with Crawl4AI support"""
    
    def __init__(self):
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.body_width = 0
        self.crawler = None
    
    def set_crawler(self, crawler):
        self.crawler = crawler

    async def fetch_with_browser(self, url: str) -> Dict[str, Any]:
        """Fetch using Crawl4AI (JavaScript rendering)"""
        # Optimized: Use global warm crawler if available
        if self.crawler:
            try:
                # Use arun directly on the warm instance
                result = await self.crawler.arun(url=url, bypass_cache=True)
                if not result.success:
                    raise Exception(result.error_message or "Crawl failed")
                return {
                    "html": result.html,
                    "markdown": result.markdown,
                    "success": True
                }
            except Exception as e:
                return {"html": "", "markdown": "", "success": False, "error": str(e)}

        # Fallback: Create new instance (Slower)
        try:
            from crawl4ai import AsyncWebCrawler
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url, bypass_cache=True)
                if not result.success:
                    raise Exception(result.error_message or "Crawl failed")
                return {
                    "html": result.html,
                    "markdown": result.markdown,
                    "success": True
                }
        except Exception as e:
            return {"html": "", "markdown": "", "success": False, "error": str(e)}
    
    async def fetch_simple(self, url: str) -> Dict[str, Any]:
        """Simple HTTP fetch without browser"""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return {"html": response.text, "success": True, "status": response.status_code}
        except Exception as e:
            return {"html": "", "success": False, "error": str(e)}
    
    def html_to_markdown(self, html: str) -> str:
        """Convert HTML to clean Markdown"""
        return self.h2t.handle(html)
    
    def extract_text(self, html: str) -> str:
        """Extract plain text"""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(" ", strip=True)
    
    def extract_metadata(self, html: str, url: str) -> Dict:
        """Extract page metadata"""
        soup = BeautifulSoup(html, "html.parser")
        return {
            "title": soup.title.get_text(strip=True) if soup.title else "",
            "description": (soup.find("meta", {"name": "description"}) or {}).get("content", ""),
            "url": url,
            "fetched_at": datetime.utcnow().isoformat()
        }
    
    def extract_links(self, html: str, base_url: str) -> List[Dict]:
        """Extract all links"""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("mailto:", "javascript:", "#")):
                continue
            full_url = urljoin(base_url, href)
            if full_url not in seen:
                seen.add(full_url)
                links.append({
                    "url": full_url,
                    "text": a.get_text(strip=True)[:100],
                    "internal": urlparse(full_url).netloc == urlparse(base_url).netloc
                })
        return links
    
    def extract_images(self, html: str, base_url: str) -> List[Dict]:
        """Extract all images"""
        soup = BeautifulSoup(html, "html.parser")
        images = []
        for img in soup.find_all("img", src=True):
            src = urljoin(base_url, img["src"])
            images.append({
                "url": src,
                "alt": img.get("alt", "")
            })
        return images

# Global instance
scraper = WebScraper()
