from fastapi import APIRouter
from ...models.api import ScrapeRequest
from ...services.scrape import mode_scrape

router = APIRouter()

@router.post("/scrape")
async def api_scrape(req: ScrapeRequest):
    """Scrape a single URL"""
    return await mode_scrape(req)
