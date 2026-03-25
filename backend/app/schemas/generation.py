from typing import List, Optional
from pydantic import BaseModel


class GenerateSingleRequest(BaseModel):
    topic: str
    platform: str = "both"
    persona_id: Optional[int] = None
    extra_instructions: str = ""


class GenerateBulkRequest(BaseModel):
    topics: List[str]
    platform: str = "both"
    persona_id: Optional[int] = None


class GenerateThreadRequest(BaseModel):
    article: str
    platform: str = "threads"  # threads or facebook
    max_chars_per_segment: int = 500
    persona_id: Optional[int] = None


class GenerateCaptionRequest(BaseModel):
    asset_id: int
    platform: str = "both"
    persona_id: Optional[int] = None
