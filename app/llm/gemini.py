import logging
from typing import Any

import httpx

from app.core.config import settings
from app.llm.client import OllamaClient

logger = logging.getLogger(__name__)


class GeminiClient(OllamaClient):
    """Gemini API adapter compatible with AgentForge's existing LLM interface."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__(model=model or settings.gemini_model)
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required when using Gemini.")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        *,
        options: dict[str, Any] | None = None,
        response_format: dict[str, Any] | str | None = None,
        think: bool | None = None,
        timeout: float = 120.0,
    ) -> str:
        del think

        generation_config: dict[str, Any] = {}
        if options and isinstance(options.get("num_predict"), int):
            generation_config["maxOutputTokens"] = options["num_predict"]

        if response_format is not None:
            generation_config["responseMimeType"] = "application/json"

        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        }
        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}],
            }
        if generation_config:
            payload["generationConfig"] = generation_config

        url = f"{self.base_url}/{self.model}:generateContent"
        try:
            response = httpx.post(
                url,
                headers={"x-goog-api-key": self.api_key},
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.error("Gemini request failed: %s", type(exc).__name__)
            raise RuntimeError(f"Gemini request failed: {type(exc).__name__}") from exc
        except ValueError as exc:
            logger.warning("Gemini returned invalid JSON.")
            raise RuntimeError("Gemini returned invalid JSON.") from exc

        try:
            candidates = data["candidates"]
            parts = candidates[0]["content"]["parts"]
            result = "".join(part["text"] for part in parts if isinstance(part.get("text"), str))
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            logger.warning("Gemini returned an invalid response structure.")
            raise RuntimeError("Gemini returned an invalid response structure.") from exc

        if not result.strip():
            raise RuntimeError("Gemini returned an empty response.")
        return result.strip()

    def health(self) -> bool:
        try:
            response = httpx.get(
                f"{self.base_url}",
                headers={"x-goog-api-key": self.api_key},
                timeout=5.0,
            )
            return response.is_success
        except httpx.HTTPError:
            return False
