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

        try:
            data = response.json()
        except ValueError as exc:
            logger.warning("Ollama returned invalid JSON.")
            raise RuntimeError("Ollama returned invalid JSON.") from exc

        if not isinstance(data, dict):
            logger.warning("Ollama returned an invalid response structure.")
            raise RuntimeError("Ollama returned an invalid response structure.")

        result = data.get("response")
        if not isinstance(result, str):
            logger.warning("Ollama response is missing a valid response field.")
            raise RuntimeError("Ollama response is missing a valid response field.")

        return result.strip()

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
        context: str | None = None,
    ) -> dict[str, Any]:
        tool_text = json.dumps(tools, indent=2)

        tool_names = [str(tool["name"]) for tool in tools if isinstance(tool.get("name"), str)]

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

        context_text = context or "No previous tool execution results."

        prompt = f"""
You are the decision engine of an AI agent.

User request:
{user_request}

Available tools:
{tool_text}

Previous execution context:
{context_text}

Follow these rules exactly:

1. Choose action "tool" when an available tool can directly perform
   the user's requested operation.
2. When action is "tool":
   - tool_name MUST be the name of the selected available tool.
   - arguments MUST contain the arguments required by that tool.
   - reason MUST be "tool_required".
3. Choose action "final" when no available tool is needed or suitable,
   or when the request has already been satisfied by previous execution.
4. When action is "final":
   - tool_name MUST be null.
   - arguments MUST be an empty object.
   - reason MUST be "no_tool_available".
5. Never combine action "final" with a tool name.
6. Never select a tool that is not listed in Available tools.
7. Do not invent tool capabilities or arguments.
8. The calculator supports arithmetic operations only. Do not assume
   that it supports exponentiation or other unsupported operations.

Examples:

Request: Calculate 17 * 23.
Decision:
{{
    "action": "tool",
    "tool_name": "calculator",
    "arguments": {{"expression": "17 * 23"}},
    "reason": "tool_required"
}}
Request: What is the current UTC date and time?
Decision:
{{"action":"tool","tool_name":"current_datetime","arguments":{{}},"reason":"tool_required"}}

Request: Hello! How are you?
Decision:
{{"action":"final","tool_name":null,"arguments":{{}},"reason":"no_tool_available"}}

Request: Calculate 2 to the power of 8.
Decision:
{{"action":"final","tool_name":null,"arguments":{{}},"reason":"no_tool_available"}}

Return ONLY the required JSON object.
Do not explain your reasoning.
""".strip()

        raw = self.generate(
            prompt,
            think=False,
            response_format=schema,
            options={
                "num_predict": 128,
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
                if tool_name is not None:
                    raise ValueError("Final action cannot select a tool.")
                if arguments:
                    raise ValueError("Final action cannot include tool arguments.")
                if reason != "no_tool_available":
                    raise ValueError("Final action requires no_tool_available.")

            if action == "tool":
                if tool_name is None:
                    raise ValueError("Tool action requires a tool name.")
                if reason != "tool_required":
                    raise ValueError("Tool action requires tool_required reason.")

                if tool_name == "calculator":
                    if set(arguments) != {"expression"}:
                        raise ValueError("Calculator requires only an expression.")
                    expression = arguments["expression"]
                    if (
                        not isinstance(expression, str)
                        or not expression.strip()
                        or len(expression) > 200
                    ):
                        raise ValueError("Invalid calculator expression argument.")
                elif tool_name == "current_datetime" and arguments:
                    raise ValueError("Current datetime does not accept arguments.")

            return {
                "action": action,
                "tool_name": tool_name,
                "arguments": arguments,
                "reason": reason,
            }

        except json.JSONDecodeError, ValueError, TypeError:
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
