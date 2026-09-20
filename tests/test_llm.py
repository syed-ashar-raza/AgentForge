from unittest.mock import Mock, patch

from app.llm.client import OllamaClient

TOOLS = [
    {
        "name": "calculator",
        "description": "Calculate a mathematical expression.",
        "dangerous": False,
    },
    {
        "name": "current_datetime",
        "description": "Return the current UTC date and time.",
        "dangerous": False,
    },
]


def test_decide_tool_final() -> None:
    client = OllamaClient()

    with patch.object(
        client,
        "generate",
        return_value=(
            '{"action":"final","tool_name":null,"arguments":{}'
            ',"reason":"no_tool_available"}'
        ),
    ):
        result = client.decide_tool(
            "What is AgentForge?",
            TOOLS,
        )

    assert result == {
        "action": "final",
        "tool_name": None,
        "arguments": {},
        "reason": "no_tool_available",
    }


def test_decide_tool_calculator() -> None:
    client = OllamaClient()

    with patch.object(
        client,
        "generate",
        return_value=(
            '{"action":"tool","tool_name":"calculator",'
            '"arguments":{"expression":"2 + 3"},'
            '"reason":"tool_required"}'
        ),
    ):
        result = client.decide_tool(
            "Calculate 2 + 3",
            TOOLS,
        )

    assert result["action"] == "tool"
    assert result["tool_name"] == "calculator"
    assert result["arguments"] == {"expression": "2 + 3"}
    assert result["reason"] == "tool_required"


def test_decide_tool_datetime() -> None:
    client = OllamaClient()

    with patch.object(
        client,
        "generate",
        return_value=(
            '{"action":"tool","tool_name":"current_datetime",'
            '"arguments":{},"reason":"tool_required"}'
        ),
    ):
        result = client.decide_tool(
            "What time is it?",
            TOOLS,
        )

    assert result["action"] == "tool"
    assert result["tool_name"] == "current_datetime"
    assert result["arguments"] == {}
    assert result["reason"] == "tool_required"


def test_decide_tool_rejects_unknown_tool() -> None:
    client = OllamaClient()

    with patch.object(
        client,
        "generate",
        return_value=(
            '{"action":"tool","tool_name":"fake_tool",'
            '"arguments":{},"reason":"tool_required"}'
        ),
    ):
        result = client.decide_tool(
            "Do something",
            TOOLS,
        )

    assert result["action"] == "final"
    assert result["tool_name"] is None
    assert result["arguments"] == {}


def test_decide_tool_handles_invalid_json() -> None:
    client = OllamaClient()

    with patch.object(
        client,
        "generate",
        return_value="not valid json",
    ):
        result = client.decide_tool(
            "Do something",
            TOOLS,
        )

    assert result["action"] == "final"
    assert result["tool_name"] is None
    assert result["arguments"] == {}


def test_generate_passes_generation_controls() -> None:
    client = OllamaClient()

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": "hello"}

    with patch(
        "app.llm.client.httpx.post",
        return_value=mock_response,
    ) as post:
        result = client.generate(
            "hello",
            options={"num_predict": 64},
            response_format={"type": "object"},
            think=False,
            timeout=30.0,
        )

    assert result == "hello"

    payload = post.call_args.kwargs["json"]

    assert payload["options"] == {"num_predict": 64}
    assert payload["format"] == {"type": "object"}
    assert payload["think"] is False
    assert post.call_args.kwargs["timeout"] == 30.0
