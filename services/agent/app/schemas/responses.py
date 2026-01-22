# services/agent/app/schemas/responses.py

from typing import List, Dict, Any
from pydantic import BaseModel


class AgentResponse(BaseModel):
    answer: str
    suggestions: List[str]
    metadata: Dict[str, Any]
