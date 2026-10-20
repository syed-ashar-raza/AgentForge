from unittest.mock import Mock, patch

import httpx
import pytest

from app.llm.gemini import GeminiClient


@pytest.fixture
def client() -> GeminiClient:
    return GeminiClient(api_key="test-key", model="gemini-test")


def test_generate_returns_text(client: GeminiClient) -> None:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "  Hello Gemini  "}]}}]
    }

    with patch("app.llm.gemini.httpx.post", return_value=response) as post:
        result = client.generate("Say hello", system="Be concise")

    assert result == "Hello Gemini"
    request = post.call_args
    assert request.args[0].endswith("/gemini-test:generateContent")
    assert request.kwargs["headers"]["x-goog-api-key"] == "test-key"
    assert request.kwargs["json"]["systemInstruction"]["parts"][0]["text"] == "Be concise"


def test_generate_requests_json_mode(client: GeminiClient) -> None:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"action":"final"}'}]}}]
    }

    with patch("app.llm.gemini.httpx.post", return_value=response) as post:
        result = client.generate(
            "Return JSON",
            response_format={"type": "object"},
            options={"num_predict": 128},
            think=False,
        )

    config = post.call_args.kwargs["json"]["generationConfig"]
    assert result == '{"action":"final"}'
    assert config["responseMimeType"] == "application/json"
    assert config["maxOutputTokens"] == 128


def test_generate_handles_http_error(client: GeminiClient) -> None:
    with patch(
        "app.llm.gemini.httpx.post",
        side_effect=httpx.ConnectError("connection refused"),
    ):
        with pytest.raises(RuntimeError, match="Gemini request failed"):
            client.generate("hello")


def test_generate_handles_invalid_json(client: GeminiClient) -> None:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = ValueError("invalid JSON")

    with patch("app.llm.gemini.httpx.post", return_value=response):
        with pytest.raises(RuntimeError, match="Gemini returned invalid JSON"):
            client.generate("hello")


def test_generate_rejects_invalid_response(client: GeminiClient) -> None:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"candidates": []}

    with patch("app.llm.gemini.httpx.post", return_value=response):
        with pytest.raises(RuntimeError, match="invalid response structure"):
            client.generate("hello")


def test_health_returns_true(client: GeminiClient) -> None:
    response = Mock()
    response.is_success = True

    with patch("app.llm.gemini.httpx.get", return_value=response) as get:
        assert client.health() is True

    assert get.call_args.kwargs["headers"]["x-goog-api-key"] == "test-key"


def test_health_returns_false_when_unavailable(client: GeminiClient) -> None:
    with patch(
        "app.llm.gemini.httpx.get",
        side_effect=httpx.ConnectError("connection refused"),
    ):
        assert client.health() is False


def test_client_requires_api_key() -> None:
    with patch("app.llm.gemini.settings.gemini_api_key", ""):
        with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
            GeminiClient(api_key="")


def test_decide_tool_uses_existing_validation(client: GeminiClient) -> None:
    with patch.object(
        client,
        "generate",
        return_value=(
            '{"action":"tool","tool_name":"fake_tool","arguments":{},"reason":"tool_required"}'
        ),
    ):
        decision = client.decide_tool(
            "Do something",
            [{"name": "calculator", "description": "Calculate", "dangerous": False}],
        )

    assert decision == {
        "action": "final",
        "tool_name": None,
        "arguments": {},
        "reason": "no_tool_available",
    }
