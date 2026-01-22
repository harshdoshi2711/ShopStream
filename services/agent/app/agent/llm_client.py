# services/agent/app/agent/llm_client.py

from openai import OpenAI
from common.config.settings import get_settings

settings = get_settings()


class LLMClient:
    """
    Thin wrapper around OpenRouter / OpenAI-compatible API.
    No business logic here.
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def classify_intent(self, user_query: str) -> str:
        """
        Return a single intent string.
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

        response = self.client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        return response.choices[0].message.content.strip()
