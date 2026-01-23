from typing import List, Optional
from dataclasses import dataclass, field


MAX_CONTEXT_RESULTS = 5


@dataclass
class ConversationContext:
    last_intent: Optional[str] = None
    last_query: Optional[str] = None
    last_result_ids: List[int] = field(default_factory=list)

    def update(
        self,
        intent: str,
        query: str,
        result_ids: List[int],
    ):
        self.last_intent = intent
        self.last_query = query
        self.last_result_ids = result_ids[:MAX_CONTEXT_RESULTS]
