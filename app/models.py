from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class Rule(BaseModel):
    type: Literal["allow", "deny"]
    pattern: str

class Selector(BaseModel):
    name: str
    selector: str
    attr: Optional[str] = None

class Limits(BaseModel):
    maxDepth: Optional[int] = None
    maxPages: Optional[int] = None
    maxDurationSeconds: Optional[int] = None

class RequestCfg(BaseModel):
    concurrency: Optional[int] = 5
    delayMs: Optional[int] = 0
    userAgent: Optional[str] = "CrawlConsole/0.1"
    respectRobots: Optional[bool] = False

class Extraction(BaseModel):
    selectors: List[Selector] = Field(default_factory=list)

class JobSpec(BaseModel):
    seeds: List[str]
    scope: Dict[str, List[Rule]] = Field(default_factory=lambda: {"rules": []})
    limits: Limits = Limits()
    request: RequestCfg = RequestCfg()
    extraction: Extraction = Extraction()
    sameDomainOnly: bool = True
    aiModel: Optional[str] = None  # OpenRouter model for AI extraction
