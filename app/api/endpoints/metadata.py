from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@router.get("/modes")
async def get_modes():
    """List available modes"""
    return {
        "modes": [
            {"name": "scrape", "description": "Extract clean markdown from any URL", "icon": "📄"},
            {"name": "search", "description": "Find content matching a query", "icon": "🔍"},
            {"name": "agent", "description": "AI-powered data extraction", "icon": "🤖"},
            {"name": "map", "description": "Map entire site structure", "icon": "🗺️"},
            {"name": "crawl", "description": "Batch crawl multiple URLs", "icon": "🕷️"}
        ]
    }

@router.get("/models")
async def get_models():
    """Available AI models"""
    return {
        "models": {
            "xiaomi/mimo-v2-flash:free": "Xiaomi MIMO v2 Flash (Free)",
            "mistralai/devstral-2512:free": "Mistral Devstral (Free)"
        }
    }
