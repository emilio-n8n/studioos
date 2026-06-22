from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import settings, OPENCODE_GO_BASE_URL

logger = logging.getLogger("studioos.cli.llm")

INPUT_COST_PER_M = 0.15
OUTPUT_COST_PER_M = 0.60


def _get_client_and_model(
    provider: str | None = None,
    model: str | None = None,
) -> tuple[AsyncOpenAI, str]:
    import os
    api_key = os.environ.get("OPENAI_API_KEY", "") or "demo"
    is_demo = api_key.strip().lower() == "demo"

    if provider == "opencode-go" or is_demo:
        base_url = OPENCODE_GO_BASE_URL
        model_name = model or "deepseek-v4-flash"
        api_key = "demo" if is_demo else api_key
    else:
        base_url = None
        model_name = model or settings.openai_model

    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=60.0)
    return client, model_name


class LLMClient:
    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
    ):
        self.provider = provider or "openai"
        self.model = model
        self._client, self._model_name = _get_client_and_model(
            provider, model
        )
        self.input_tokens: int = 0
        self.output_tokens: int = 0

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        on_token: callable = None,
    ) -> str:
        full_response = ""
        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=4096,
            )

            async for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    token = delta.content
                    full_response += token
                    if on_token:
                        await on_token(token)

                if chunk.usage:
                    self.input_tokens += chunk.usage.prompt_tokens or 0
                    self.output_tokens += (
                        chunk.usage.completion_tokens or 0
                    )

        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            raise

        return full_response

    async def chat(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                stream=False,
                temperature=0.7,
                max_tokens=4096,
            )

            content = response.choices[0].message.content or ""
            if response.usage:
                self.input_tokens += response.usage.prompt_tokens or 0
                self.output_tokens += (
                    response.usage.completion_tokens or 0
                )

            return content

        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise

    def get_token_summary(self) -> dict[str, Any]:
        total = self.input_tokens + self.output_tokens
        cost = (
            self.input_tokens / 1_000_000 * INPUT_COST_PER_M
            + self.output_tokens / 1_000_000 * OUTPUT_COST_PER_M
        )
        return {
            "input": self.input_tokens,
            "output": self.output_tokens,
            "total": total,
            "estimated_cost": round(cost, 4),
        }
