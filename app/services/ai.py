import os
from typing import Dict, Any
from ..models.api import AgentRequest
from .crawler import scraper

async def mode_agent(req: AgentRequest) -> Dict[str, Any]:
    """
    AGENT MODE: AI-powered intelligent extraction
    - Uses OpenRouter models
    - Custom instructions
    - Structured output
    """
    result = await scraper.fetch_with_browser(req.url)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "mode": "agent"}
    
    content = result.get("markdown") or scraper.extract_text(result["html"])
    content = content[:8000]  # Truncate for token limits
    
    # Check for API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return {
            "success": False,
            "mode": "agent",
            "error": "OPENROUTER_API_KEY not set. Set it to use AI extraction.",
            "url": req.url
        }
    
    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIModel
        
        # Use OpenAIModel directly with custom base_url for OpenRouter
        model = OpenAIModel(
            req.model,
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        agent = Agent(
            model,
            instructions="You are a data extraction agent. Follow the user's instructions precisely."
        )
        
        prompt = f"""Instruction: {req.instruction}

Content from {req.url}:
{content}

Extract the requested information and respond in JSON format."""
        
        ai_result = await agent.run(prompt)
        
        return {
            "success": True,
            "mode": "agent",
            "url": req.url,
            "instruction": req.instruction,
            "model": req.model,
            "extracted": ai_result.output
        }
    except Exception as e:
        return {
            "success": False,
            "mode": "agent",
            "url": req.url,
            "error": str(e)
        }
