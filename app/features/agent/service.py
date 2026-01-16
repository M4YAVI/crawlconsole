"""
Agent Feature Service
"""
import os
import json
import traceback
from typing import Dict, Any, Optional
from ...models.api import AgentRequest
from ...services.scraper import scraper
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError

async def mode_agent(req: AgentRequest) -> Dict[str, Any]:
    """
    AGENT MODE: AI-powered intelligent extraction with OpenRouter
    
    Supported models:
    - anthropic/claude-3.5-sonnet (Recommended)
    - meta-llama/llama-3.3-70b-instruct (Free!)
    - mistralai/mistral-large
    - openai/gpt-4-turbo
    """
    
    # Validate request
    if not req.url or not req.instruction:
        return {
            "success": False,
            "mode": "agent",
            "error": "Missing url or instruction"
        }
    
    # Fetch content
    result = await scraper.fetch_with_browser(req.url)
    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error"),
            "mode": "agent",
            "url": req.url
        }
    
    # Extract content
    content = result.get("markdown") or scraper.extract_text(result["html"])
    if not content:
        return {
            "success": False,
            "error": "No content extracted from URL",
            "mode": "agent",
            "url": req.url
        }
    
    content = content[:8000]  # Truncate for token limits
    
    # Validate API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return {
            "success": False,
            "mode": "agent",
            "error": "OPENROUTER_API_KEY environment variable not set",
            "hint": "Set: export OPENROUTER_API_KEY='your-key'"
        }
    
    try:
        # ✅ Configure OpenRouter provider
        provider = OpenRouterProvider(
            api_key=api_key,
            app_url=os.environ.get("OPENROUTER_APP_URL"),
            app_title=os.environ.get("OPENROUTER_APP_TITLE", "WebScraper")
        )
        
        # ✅ Create OpenRouter model
        model = OpenRouterModel(
            req.model or "anthropic/claude-3.5-sonnet",
            provider=provider
        )
        
        # Optional: Configure model settings
        settings = OpenRouterModelSettings(
            temperature=0.3,  # Lower for consistent extraction
            max_tokens=2048,
        )
        
        # Create agent
        agent = Agent(
            model,
            instructions=(
                "You are a precise data extraction expert. "
                "Extract ONLY the requested information. "
                "Return valid JSON. Be accurate and concise."
            ),
            model_settings=settings
        )
        
        # Build extraction prompt
        prompt = f"""Extract Information Request
==========================================
Task: {req.instruction}

Source: {req.url}

Content to analyze:
{content}

Guidelines:
1. Extract ONLY what was requested
2. Return valid JSON format
3. If information not found, indicate as null
4. Be precise and accurate
5. Use the exact structure requested"""
        
        # Run agent
        ai_result = await agent.run(prompt)
        
        # Parse response
        extracted = _parse_response(ai_result.output)
        
        return {
            "success": True,
            "mode": "agent",
            "url": req.url,
            "instruction": req.instruction,
            "model": req.model,
            "extracted": extracted,
            "content_length": len(content),
            "response_length": len(str(ai_result.output))
        }
        
    except ModelAPIError as e:
        return {
            "success": False,
            "mode": "agent",
            "url": req.url,
            "error": f"OpenRouter API Error: {str(e)}",
            "error_type": "api_error"
        }
    except ModelHTTPError as e:
        return {
            "success": False,
            "mode": "agent",
            "url": req.url,
            "error": f"HTTP Error {e.status_code}: {e}",
            "error_type": "http_error"
        }
    except Exception as e:
        return {
            "success": False,
            "mode": "agent",
            "url": req.url,
            "error": str(e),
            "error_type": "unknown",
            "traceback": traceback.format_exc() if os.environ.get("DEBUG") else None
        }

def _parse_response(response: str) -> Dict[str, Any]:
    """Parse AI response - try JSON first, fallback to raw."""
    if not response:
        return {}
    
    # Try JSON parsing
    try:
        if isinstance(response, dict):
            return response
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from response
    if isinstance(response, str) and "{" in response and "}" in response:
        try:
            start = response.index("{")
            end = response.rindex("}") + 1
            return json.loads(response[start:end])
        except (ValueError, json.JSONDecodeError):
            pass
    
    return {"raw_response": response}
