from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ...models.api import CrawlRequest
from ...services.crawl import mode_crawl, mode_crawl_stream

router = APIRouter()

@router.post("/crawl")
async def api_crawl(req: CrawlRequest):
    """Batch crawl URLs"""
    return await mode_crawl(req)

@router.post("/crawl/stream")
async def api_crawl_stream(req: CrawlRequest):
    """Stream crawl results"""
    return StreamingResponse(
        mode_crawl_stream(req),
        media_type="application/x-ndjson"
    )
