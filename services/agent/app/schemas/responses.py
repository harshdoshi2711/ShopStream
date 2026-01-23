# services/agent/app/schemas/responses.py

from pydantic import BaseModel
from typing import List, Dict, Any


class AgentMetadata(BaseModel):
    intent: str
    result_count: int
    fallback_used: bool


class AgentResponse(BaseModel):
    answer: str
    suggestions: List[Any]
    metadata: AgentMetadata
