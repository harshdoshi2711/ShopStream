# services/agent/app/schemas/responses.py

from pydantic import BaseModel, Field
from typing import List, Any


class AgentMetadata(BaseModel):
    """
    Metadata about how the agent handled the request.
    """

    intent: str = Field(..., description="Final resolved intent")
    result_count: int = Field(..., description="Number of items returned")
    fallback_used: bool = Field(
        ..., description="True if agent used a safe fallback response"
    )


class AgentResponse(BaseModel):
    """
    Stable API contract for ShopAgent responses.

    Guarantees:
    - Always valid JSON
    - suggestions is ALWAYS a list
    """

    answer: str = Field(..., description="Natural language response")
    suggestions: List[Any] = Field(
        default_factory=list,
        description="Structured results (products, orders, etc.)",
    )
    metadata: AgentMetadata
