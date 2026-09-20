import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model

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
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if system:
            payload["system"] = system

        if options:
            payload["options"] = options

        if response_format is not None:
            payload["format"] = response_format

        if think is not None:
            payload["think"] = think

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("Ollama request failed.")
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        return str(data.get("response", "")).strip()

    def health(self) -> bool:
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=5.0,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    def decide_tool(
        self,
        user_request: str,
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        tool_text = json.dumps(tools, indent=2)

        tool_names = [
            str(tool["name"])
            for tool in tools
            if isinstance(tool.get("name"), str)
        ]

        tool_name_schema: dict[str, Any] = {
            "anyOf": [
                {
                    "type": "string",
                    "enum": tool_names,
                },
                {
                    "type": "null",
                },
            ]
        }

        schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["tool", "final"],
                },
                "tool_name": tool_name_schema,
                "arguments": {
                    "type": "object",
                },
                "reason": {
                    "type": "string",
                    "enum": [
                        "tool_required",
                        "no_tool_available",
                    ],
                },
            },
            "required": [
                "action",
                "tool_name",
                "arguments",
                "reason",
            ],
        }

        prompt = f"""
You are the decision engine of an AI agent.

User request:
{user_request}

Available tools:
{tool_text}

Select a tool only if one of the available tools can directly satisfy the request.
Otherwise select final.

Return ONLY the required JSON object.
Do not explain your reasoning.
""".strip()

        raw = self.generate(
            prompt,
            think=False,
            response_format=schema,
            options={
                "num_predict": 64,
            },
            timeout=30.0,
        )

        try:
            decision = json.loads(raw)

            if not isinstance(decision, dict):
                raise ValueError("Decision must be a JSON object.")

            action = decision.get("action")
            tool_name = decision.get("tool_name")
            arguments = decision.get("arguments")
            reason = decision.get("reason")

            if action not in {"tool", "final"}:
                raise ValueError("Invalid decision action.")

            if tool_name is not None and tool_name not in tool_names:
                raise ValueError("Model selected an unregistered tool.")

            if not isinstance(arguments, dict):
                raise ValueError("Decision arguments must be an object.")

            if reason not in {
                "tool_required",
                "no_tool_available",
            }:
                raise ValueError("Invalid decision reason.")

            if action == "final":
                tool_name = None

            if action == "tool" and tool_name is None:
                raise ValueError("Tool action requires a tool name.")

            return {
                "action": action,
                "tool_name": tool_name,
                "arguments": arguments,
                "reason": reason,
            }

        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning(
                "Invalid tool decision from model: %s",
                raw,
            )
            return {
                "action": "final",
                "tool_name": None,
                "arguments": {},
                "reason": "no_tool_available",
            }

