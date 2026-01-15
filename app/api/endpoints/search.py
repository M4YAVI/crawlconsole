from fastapi import APIRouter
from ...models.api import SearchRequest
from ...services.search import mode_search

router = APIRouter()

@router.post("/search")
async def api_search(req: SearchRequest):
    """Search content on a page"""
    return await mode_search(req)
