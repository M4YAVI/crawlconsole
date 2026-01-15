from fastapi import APIRouter
from ...models.api import MapRequest
from ...services.map import mode_map

router = APIRouter()

@router.post("/map")
async def api_map(req: MapRequest):
    """Map site structure"""
    return await mode_map(req)
