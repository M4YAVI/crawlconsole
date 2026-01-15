from fastapi import APIRouter
from ...models.api import AgentRequest
from ...services.ai import mode_agent

router = APIRouter()

@router.post("/agent")
async def api_agent(req: AgentRequest):
    """AI-powered extraction"""
    return await mode_agent(req)
