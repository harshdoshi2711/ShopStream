# services/agent/app/agent/llm_client.py

import logging
from openai import OpenAI, OpenAIError

from common.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger("shopstream.shopagent.llm")


class LLMClient:
    """
    Hardened wrapper around OpenRouter / OpenAI-compatible API.

    Rules:
    - LLM is used ONLY for first-turn intent classification
    - Follow-ups like "show more" must NOT reach the LLM
    - Never raises
    """

    ALLOWED_INTENTS = {
        "TRENDING_PRODUCTS",
        "FILTER_PRODUCTS",
        "ORDER_STATUS",
        "SUGGEST_ALTERNATIVES",
        "UNKNOWN",
    }

    FOLLOWUP_KEYWORDS = {
        "show more",
        "more",
        "continue",
        "next",
        "what else",
    }

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=5.0,
        )

    def classify_intent(self, user_query: str) -> str:
        """
        Classify user intent.

        Guarantees:
        - Follow-ups NEVER hit the LLM
        - Always returns a valid intent
        """

        normalized = user_query.lower().strip()

        # 🔒 HARD GUARD: follow-ups never go to LLM
        if normalized in self.FOLLOWUP_KEYWORDS:
            logger.info(
                "Follow-up detected, skipping LLM",
                extra={"query": user_query},
            )
            return "UNKNOWN"

        prompt = f"""
You are an intent classifier for an e-commerce assistant.

Choose EXACTLY ONE intent from:
- TRENDING_PRODUCTS
- FILTER_PRODUCTS
- ORDER_STATUS
- SUGGEST_ALTERNATIVES
- UNKNOWN

User query:
\"\"\"{user_query}\"\"\"  

Respond with ONLY the intent name.
"""

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )

            raw_intent = response.choices[0].message.content.strip().upper()

            if raw_intent not in self.ALLOWED_INTENTS:
                logger.warning(
                    "LLM returned unsupported intent",
                    extra={"raw_intent": raw_intent},
                )
                return "UNKNOWN"

            logger.info(
                "LLM intent classification succeeded",
                extra={"intent": raw_intent},
            )

            return raw_intent

        except OpenAIError as e:
            logger.error(
                "LLM request failed",
                extra={"error": str(e)},
            )
            return "UNKNOWN"

        except Exception as e:
            logger.exception(
                "Unexpected LLM failure",
                extra={"error": str(e)},
            )
            return "UNKNOWN"
