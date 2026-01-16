from fastapi import APIRouter
from ...models.api import ScrapeRequest
from ...services.scraper import scraper
from ...features.scrape.service import mode_scrape

router = APIRouter()

@router.post("/scrape")
async def api_scrape(req: ScrapeRequest):
    """Scrape a single URL"""
    return await mode_scrape(req)
