import asyncio
import aiohttp
import re
import time
from collections import deque
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple
from urllib.parse import urljoin, urldefrag, urlparse
from bs4 import BeautifulSoup
from robotexclusionrulesparser import RobotExclusionRulesParser
from crawl4ai import AsyncWebCrawler

from .db import insert_result, update_job

class RobotsCache:
    def __init__(self):
        self._cache: Dict[str, RobotExclusionRulesParser] = {}

    async def allowed(self, session: aiohttp.ClientSession, url: str, user_agent: str) -> bool:
        host = urlparse(url).netloc
        if host not in self._cache:
            robots_url = f"{urlparse(url).scheme}://{host}/robots.txt"
            parser = RobotExclusionRulesParser()
            try:
                async with session.get(robots_url, timeout=10) as r:
                    txt = await r.text()
                    parser.parse(txt)
            except Exception:
                parser.parse("")  # if robots fails, allow all
            self._cache[host] = parser
        return self._cache[host].is_allowed(user_agent, url)

def compile_rules(rules: List[Dict[str, str]]) -> Tuple[List[re.Pattern], List[re.Pattern]]:
    allow = []
    deny = []
    for r in rules:
        try:
            pat = re.compile(r["pattern"])
            if r["type"] == "allow":
                allow.append(pat)
            else:
                deny.append(pat)
        except Exception:
            continue
    return allow, deny

def in_scope(url: str, allow: List[re.Pattern], deny: List[re.Pattern]) -> bool:
    for d in deny:
        if d.search(url):
            return False
    if not allow:
        return True
    return any(a.search(url) for a in allow)

def same_domain(url: str, seed_hosts: Set[str]) -> bool:
    return urlparse(url).netloc in seed_hosts

def extract_links(base_url: str, html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        try:
            u = urljoin(base_url, href)
            u, _ = urldefrag(u)
            urls.append(u)
        except:
            continue
    return urls

def extract_selectors(html: str, selectors: List[Dict[str, Any]]) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for sel in selectors:
        name = sel["name"]
        css = sel["selector"]
        attr = sel.get("attr")
        try:
            nodes = soup.select(css)
            if attr:
                out[name] = [n.get(attr) for n in nodes if n.get(attr) is not None]
            else:
                out[name] = [n.get_text(" ", strip=True) for n in nodes]
        except:
            out[name] = []
    return out

async def crawl_job(job_id: str, spec: Dict[str, Any], cancel_flag: asyncio.Event):
    seeds = spec["seeds"]
    rules = spec.get("scope", {}).get("rules", [])
    limits = spec.get("limits", {})
    request = spec.get("request", {})
    extraction = spec.get("extraction", {})
    selectors = extraction.get("selectors", [])
    same_domain_only = spec.get("sameDomainOnly", True)

    max_depth = limits.get("maxDepth")
    max_pages = limits.get("maxPages")
    max_duration = limits.get("maxDurationSeconds")

    concurrency = request.get("concurrency") or 2 # default slightly lower for browser
    delay_ms = request.get("delayMs") or 0
    user_agent = request.get("userAgent") or "CrawlConsole/0.1"
    respect_robots = request.get("respectRobots") or False

    allow, deny = compile_rules(rules)
    seed_hosts = {urlparse(s).netloc for s in seeds}

    q = deque([(s, 0) for s in seeds])
    seen: Set[str] = set()
    pages = 0
    start = time.time()

    robots = RobotsCache()

    timeout = aiohttp.ClientTimeout(total=20)
    headers = {"User-Agent": user_agent}

    # We use aiohttp for robots.txt fetching
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        # We use AsyncWebCrawler for fetching the actual pages
        async with AsyncWebCrawler(verbose=True) as crawler:
            sem = asyncio.Semaphore(concurrency)

            async def fetch(url: str, depth: int):
                nonlocal pages
                if cancel_flag.is_set():
                    return
                # Check constraints
                if url in seen: return
                if max_depth is not None and depth > max_depth: return
                if max_pages is not None and pages >= max_pages: return
                if max_duration is not None and (time.time() - start) > max_duration: return
                if not in_scope(url, allow, deny): return
                if same_domain_only and not same_domain(url, seed_hosts): return

                seen.add(url)
                
                await sem.acquire()
                try:
                    if respect_robots:
                        allowed = await robots.allowed(session, url, user_agent)
                        if not allowed:
                            return
                            
                    if delay_ms:
                        await asyncio.sleep(delay_ms / 1000.0)

                    # Crawl4AI fetch
                    try:
                        # Bypass cache to ensure we carry out the request
                        result = await crawler.arun(url=url, bypass_cache=True)
                        
                        if not result.success:
                             raise Exception(result.error_message or "Unknown crawl error")
                        
                        html = result.html
                        markdown = result.markdown
                        
                        # Process content
                        links = extract_links(url, html)
                        extracted = extract_selectors(html, selectors)
                        
                        soup = BeautifulSoup(html, "html.parser")
                        title = soup.title.get_text(strip=True) if soup and soup.title else None
                        text = soup.get_text(" ", strip=True) if soup else None
                        
                        await insert_result(job_id, {
                            "url": url,
                            "status_code": 200, # Crawl4AI doesn't always expose status easily in basic result, assumes success
                            "depth": depth,
                            "fetched_at": datetime.utcnow().isoformat(),
                            "content_type": "text/html",
                            "title": title,
                            "text": text,
                            "html": html,
                            "markdown": markdown,
                            "links": links,
                            "extracted": extracted
                        })

                        pages += 1
                        for link in links:
                            if link not in seen:
                                q.append((link, depth + 1))
                                
                    except Exception as e:
                        await insert_result(job_id, {
                            "url": url,
                            "status_code": 0,
                            "depth": depth,
                            "fetched_at": datetime.utcnow().isoformat(),
                            "content_type": None,
                            "title": None,
                            "text": None,
                            "html": None,
                            "markdown": None,
                            "links": [],
                            "extracted": {},
                            "error": str(e)
                        })

                finally:
                    sem.release()

            tasks = set()
            while q:
                if cancel_flag.is_set():
                    break
                
                # Check limits again in loop
                if max_pages is not None and pages >= max_pages:
                    break
                if max_duration is not None and (time.time() - start) > max_duration:
                    break

                # Pop next
                url, depth = q.popleft()
                
                # Launch task
                t = asyncio.create_task(fetch(url, depth))
                tasks.add(t)
                t.add_done_callback(tasks.discard)
                
                # Simple throttle loop if too many tasks (bounded by semaphore but also q size)
                # But here we just let semaphore handle access to browser
                if len(tasks) >= concurrency * 2:
                    await asyncio.sleep(0.1)
                else:
                     await asyncio.sleep(0.01) # Yield slightly

            if tasks:
                await asyncio.gather(*tasks)

    stats = {
        "pages": pages,
        "seen": len(seen),
        "durationSeconds": round(time.time() - start, 2)
    }
    await update_job(job_id, stats_json=str(stats))
