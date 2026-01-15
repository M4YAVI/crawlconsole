"""
AI Extraction Service using Pydantic AI + OpenRouter

Provides AI-powered content summarization and extraction using free OpenRouter models.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field

# Available free models
AVAILABLE_MODELS = {
    "xiaomi/mimo-v2-flash:free": "Xiaomi MIMO v2 Flash (Free)",
    "mistralai/devstral-2512:free": "Mistral Devstral (Free)",
}

DEFAULT_MODEL = "xiaomi/mimo-v2-flash:free"

class ExtractionResult(BaseModel):
    """Result from AI extraction."""
    summary: str = Field(..., description="Brief summary of the page content")
    key_points: list[str] = Field(default_factory=list, description="Main points from the content")
    topics: list[str] = Field(default_factory=list, description="Topics covered")
    sentiment: str = Field(default="neutral", description="Overall sentiment: positive, negative, or neutral")

async def extract_with_ai(
    content: str,
    url: str,
    model_name: str = DEFAULT_MODEL,
    api_key: Optional[str] = None
) -> Optional[ExtractionResult]:
    """
    Extract structured information from page content using AI.
    
    Args:
        content: The text content to analyze
        url: Source URL for context
        model_name: OpenRouter model to use
        api_key: OpenRouter API key (optional if env var set)
    
    Returns:
        ExtractionResult or None if extraction fails
    """
    # Check for API key
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    
    try:
        from pydantic_ai import Agent
        from pydantic_ai.providers.openai import OpenAIProvider
        
        # Create OpenRouter provider (uses OpenAI-compatible API)
        provider = OpenAIProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
        )
        
        # Create agent with structured output
        agent = Agent(
            model_name,
            provider=provider,
            output_type=ExtractionResult,
            instructions=(
                "You are a content extraction agent. Analyze the given web page content "
                "and extract structured information. Be concise and accurate."
            ),
        )
        
        # Truncate content if too long (most free models have token limits)
        max_chars = 8000
        truncated = content[:max_chars] if len(content) > max_chars else content
        
        # Run extraction
        prompt = f"Analyze this content from {url}:\n\n{truncated}"
        result = await agent.run(prompt)
        
        return result.output
        
    except Exception as e:
        print(f"[AI Extraction Error] {e}")
        return None

def get_available_models() -> dict:
    """Return available model options."""
    return AVAILABLE_MODELS
