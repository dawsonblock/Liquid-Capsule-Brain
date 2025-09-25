"""DeepSeek V3 API client for Liquid Capsule Brain."""

from __future__ import annotations

import asyncio
import logging
import os
import random
from typing import Any

from openai import APIError, OpenAI

log = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek V3 API client using OpenAI-compatible interface."""

    def __init__(self) -> None:
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com"
        self.model = "deepseek-chat"
        
        # Retry configuration
        self.max_retries = int(os.getenv("DEEPSEEK_MAX_RETRIES", "3"))
        self.base_delay = float(os.getenv("DEEPSEEK_BASE_DELAY", "1.0"))
        self.max_delay = float(os.getenv("DEEPSEEK_MAX_DELAY", "60.0"))
        self.timeout = float(os.getenv("DEEPSEEK_TIMEOUT", "30.0"))

        if not self.api_key:
            log.warning("DEEPSEEK_API_KEY not found in environment")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
            log.info("DeepSeek V3 client initialized with retry logic")

    def is_available(self) -> bool:
        """Check if DeepSeek API is available."""
        return self.client is not None

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry a function with exponential backoff and jitter."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except (APIError, Exception) as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    log.error(f"Max retries ({self.max_retries}) exceeded for DeepSeek API call")
                    raise e
                
                # Calculate delay with exponential backoff and jitter
                delay = min(
                    self.base_delay * (2 ** attempt) + random.uniform(0, 1),
                    self.max_delay
                )
                
                log.warning(f"DeepSeek API call failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}. Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
        
        raise last_exception

    async def generate_response(
        self, context: str, system_prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> dict[str, Any]:
        """Generate a response using DeepSeek V3."""

        if not self.client:
            return {
                "text": "[DeepSeek Unavailable] No API key configured.",
                "model": "fallback",
                "usage": {"total_tokens": 0},
            }

        async def _make_request():
            messages: list[dict[str, str]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context},
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
            )

            return {
                "text": response.choices[0].message.content or "",
                "model": response.model,
                "finish_reason": getattr(response.choices[0], "finish_reason", None),
                "usage": {
                    "prompt_tokens": (response.usage.prompt_tokens if response.usage else 0),
                    "completion_tokens": (
                        response.usage.completion_tokens if response.usage else 0
                    ),
                    "total_tokens": (response.usage.total_tokens if response.usage else 0),
                },
            }

        try:
            return await self._retry_with_backoff(_make_request)
        except APIError as exc:
            log.error("DeepSeek API error after retries: %s", exc)
            return {
                "text": f"[DeepSeek API Error] {exc.message or str(exc)}",
                "model": "error",
                "usage": {"total_tokens": 0},
            }
        except Exception as exc:
            log.error("DeepSeek unexpected error after retries: %s", exc)
            return {
                "text": f"[DeepSeek Error] Unexpected error: {str(exc)}",
                "model": "error",
                "usage": {"total_tokens": 0},
            }

    async def stream_response(
        self, context: str, system_prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> Any:
        """Stream a response using DeepSeek V3."""

        if not self.client:
            yield {"text": "[DeepSeek Unavailable] No API key configured.", "done": True}
            return

        try:
            messages: list[dict[str, str]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context},
            ]

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {"text": chunk.choices[0].delta.content, "done": False}

            yield {"text": "", "done": True}

        except Exception as exc:
            log.error("DeepSeek streaming error: %s", exc)
            yield {"text": f"[DeepSeek Error] Streaming failed: {str(exc)}", "done": True}
