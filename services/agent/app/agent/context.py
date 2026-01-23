# services/agent/app/agent/context.py

from typing import List, Optional
from dataclasses import dataclass, field

MAX_CONTEXT_RESULTS = 20
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

    recent_intents: List[str] = field(default_factory=list)
    recent_queries: List[str] = field(default_factory=list)

    def update(
        self,
        intent: str,
        query: str,
        result_ids: List[int],
    ):
        self.last_intent = intent
        self.last_query = query

        # 🔒 CRITICAL FIX: accumulate, never wipe on empty
        if result_ids:
            combined = self.last_result_ids + result_ids
            # dedupe while preserving order
            seen = set()
            self.last_result_ids = [
                x for x in combined
                if not (x in seen or seen.add(x))
            ][:MAX_CONTEXT_RESULTS]

        # rolling history
        self.recent_intents.insert(0, intent)
        self.recent_queries.insert(0, query)

        self.recent_intents = self.recent_intents[:MAX_CONTEXT_TURNS]
        self.recent_queries = self.recent_queries[:MAX_CONTEXT_TURNS]
