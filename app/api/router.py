from fastapi import APIRouter
from .endpoints import scrape, search, agent, map, crawl, metadata

router = APIRouter()

# Include all feature sub-routers
router.include_router(metadata.router, tags=["Metadata"])
router.include_router(scrape.router, tags=["Scrape"])
router.include_router(search.router, tags=["Search"])
router.include_router(agent.router, tags=["Agent"])
router.include_router(map.router, tags=["Map"])
router.include_router(crawl.router, tags=["Crawl"])
