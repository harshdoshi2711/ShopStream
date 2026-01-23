# services/agent/app/agent/llm_client.py

import logging
from openai import OpenAI, OpenAIError
from common.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger("shopstream.shopagent.llm")


class LLMClient:
    """
    Hardened wrapper around OpenRouter / OpenAI-compatible API.
    The LLM is treated as an unreliable dependency.
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=5.0,  # 🔒 HARD TIMEOUT (seconds)
        )

    def classify_intent(self, user_query: str) -> str:
        """
        Return a single intent string.
        Never raises exceptions.
        """

        prompt = f"""
You are a classifier for an e-commerce assistant.

Choose ONE intent from this list:
- TRENDING_PRODUCTS
- FILTER_PRODUCTS
- ORDER_STATUS
- SUGGEST_ALTERNATIVES
- UNKNOWN

User query:
\"\"\"{user_query}\"\"\"

Respond with ONLY the intent.
"""

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )

            intent = response.choices[0].message.content.strip()

            logger.info(
                "LLM intent classification succeeded",
                extra={"intent": intent},
            )

            return intent

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
