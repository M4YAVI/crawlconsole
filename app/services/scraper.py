"""
Complete Scraper Implementation with Real Web Crawling
"""
import re
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import traceback
from playwright.async_api import async_playwright
from markdownify import markdownify as md

logger = logging.getLogger(__name__)

class Scraper:
    """Complete scraper with all methods implemented"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    async def fetch_with_browser(self, url: str) -> Dict[str, Any]:
        """Fetch using Playwright (handles JavaScript)"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-infobars",
                        "--window-position=0,0",
                        "--ignore-certificate-errors",
                        "--ignore-certificate-errors-spki-list",
                        "--disable-accelerated-2d-canvas",
                        "--disable-gpu",
                    ]
                )
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1920, "height": 1080},
                    java_script_enabled=True,
                )
                page = await context.new_page()
                
                # Add init script to mask webdriver
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    # Wait a bit for loose scripts
                    await page.wait_for_timeout(2000)
                except Exception:
                    # If specific wait fails, we might still have content
                    pass
                
                html = await page.content()
                markdown = await self._html_to_markdown_async(html)
                
                await browser.close()
                
                return {
                    "success": True,
                    "html": html,
                    "markdown": markdown,
                    "url": url
                }
        except Exception as e:
            logger.error(f"Browser fetch failed for {url}: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": f"{str(e)}: {traceback.format_exc()}",
                "url": url
            }
    
    async def fetch_simple(self, url: str) -> Dict[str, Any]:
        """Fetch using simple HTTP (no JavaScript)"""
        try:
            if self.session is None:
                self.session = aiohttp.ClientSession()
            
            headers = {"User-Agent": self.user_agent}
            
            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "url": url
                    }
                
                html = await response.text()
                markdown = self.html_to_markdown(html)
                
                return {
                    "success": True,
                    "html": html,
                    "markdown": markdown,
                    "url": url
                }
        except Exception as e:
            logger.error(f"Simple fetch failed for {url}: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": f"{str(e)}: {traceback.format_exc()}",
                "url": url
            }
    
    def extract_metadata(self, html: str, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            else:
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    title = og_title.get('content', '').strip()
            
            # Description
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
            else:
                og_desc = soup.find('meta', property='og:description')
                if og_desc:
                    description = og_desc.get('content', '').strip()
            
            # Author
            author = ""
            author_tag = soup.find('meta', attrs={'name': 'author'})
            if author_tag:
                author = author_tag.get('content', '').strip()
            
            # Keywords
            keywords = ""
            keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_tag:
                keywords = keywords_tag.get('content', '').strip()
            
            # Favicon
            favicon = ""
            icon_tag = soup.find('link', rel='icon')
            if icon_tag:
                favicon = icon_tag.get('href', '')
                if favicon and not favicon.startswith('http'):
                    favicon = urljoin(url, favicon)
            
            return {
                "title": title,
                "description": description,
                "author": author,
                "keywords": keywords,
                "favicon": favicon,
                "url": url
            }
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return {"title": "", "description": "", "author": "", "keywords": "", "favicon": "", "url": url}
    
    def html_to_markdown(self, html: str, include_links: bool = False, include_images: bool = False) -> str:
        """Convert HTML to markdown using markdownify and cleaning"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Semantic cleaning: Remove noise elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                tag.decompose()
            
            # Additional heuristic noise removal
            for tag in soup.find_all(attrs={"class": re.compile(r"(ad|banner|cookie|popup|subscription|login-modal)", re.I)}):
                tag.decompose()
                
            # Filter links if not requested
            if not include_links:
                for tag in list(soup.find_all('a')):
                    tag.unwrap() # Removes the tag but keeps text
                    
            # Filter images if not requested
            if not include_images:
                for tag in list(soup.find_all('img')):
                    tag.decompose() # Removes message completely
            
            # Convert to Markdown (ATX style headers are standard #)
            # We strip buttons/inputs as they are usually not content
            clean_html = str(soup)
            markdown = md(clean_html, heading_style="ATX", strip=['script', 'style', 'button', 'input', 'form'])
            
            # Post-processing to remove excessive newlines
            markdown = re.sub(r'\n{3,}', '\n\n', markdown).strip()
            
            return markdown
        except Exception as e:
            logger.warning(f"Failed to convert HTML to markdown: {e}")
            return html
    
    async def _html_to_markdown_async(self, html: str) -> str:
        """Async wrapper for html_to_markdown"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.html_to_markdown, html)
    
    def extract_text(self, html: str) -> str:
        """Extract clean text from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Semantic cleaning for text too
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                tag.decompose()
            
            text = soup.get_text(separator=' ')
            
            # Collapse multiple spaces
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
        except Exception as e:
            logger.warning(f"Failed to extract text: {e}")
            return ""
    
    def extract_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract all links from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').strip()
                text = link.get_text().strip()
                
                # Skip empty hrefs
                if not href:
                    continue
                
                # Convert relative URLs to absolute
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                links.append({
                    "url": href,
                    "text": text or href
                })
            
            # Remove duplicates
            unique_links = []
            seen_urls = set()
            for link in links:
                if link["url"] not in seen_urls:
                    unique_links.append(link)
                    seen_urls.add(link["url"])
            
            return unique_links
        except Exception as e:
            logger.warning(f"Failed to extract links: {e}")
            return []
    
    def extract_images(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract all images from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            images = []
            
            for img in soup.find_all('img'):
                src = img.get('src', '').strip()
                alt = img.get('alt', '').strip()
                title = img.get('title', '').strip()
                
                # Skip empty src
                if not src:
                    continue
                
                # Convert relative URLs to absolute
                if not src.startswith('http'):
                    src = urljoin(base_url, src)
                
                images.append({
                    "src": src,
                    "alt": alt,
                    "title": title
                })
            
            return images
        except Exception as e:
            logger.warning(f"Failed to extract images: {e}")
            return []
    
    async def startup(self):
        """Initialize resources"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """Close aiohttp session and cleanup resources"""
        if self.session:
            await self.session.close()

# Singleton instance
scraper = Scraper()
