"""
llm_client.py — Anthropic Claude API wrapper with retry logic.
"""
from __future__ import annotations
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import get_settings

settings = get_settings()


class LLMClient:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int | None = None,
    ) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens or settings.llm_max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text
