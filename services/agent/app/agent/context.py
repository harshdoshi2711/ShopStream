# services/agent/app/agent/context.py

from typing import List, Optional
from dataclasses import dataclass, field

MAX_CONTEXT_RESULTS = 5
MAX_CONTEXT_TURNS = 3


@dataclass
class ConversationContext:
    """
    Lightweight, bounded conversational memory.
    Intentionally NOT persisted.
    """

    last_intent: Optional[str] = None
    last_query: Optional[str] = None
    last_result_ids: List[int] = field(default_factory=list)

    # rolling memory (most recent first)
    recent_intents: List[str] = field(default_factory=list)
    recent_queries: List[str] = field(default_factory=list)

    def update(
        self,
        intent: str,
        query: str,
        result_ids: List[int],
    ):
        # primary memory
        self.last_intent = intent
        self.last_query = query
        self.last_result_ids = result_ids[:MAX_CONTEXT_RESULTS]

        # rolling intent/query history
        self.recent_intents.insert(0, intent)
        self.recent_queries.insert(0, query)

        self.recent_intents = self.recent_intents[:MAX_CONTEXT_TURNS]
        self.recent_queries = self.recent_queries[:MAX_CONTEXT_TURNS]

    def recently_used_intent(self, intent: str) -> bool:
        return intent in self.recent_intents

    def has_seen_result(self, result_id: int) -> bool:
        return result_id in self.last_result_ids
