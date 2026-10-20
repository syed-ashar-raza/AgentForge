from unittest.mock import Mock

import pytest

from app.agent.agent import Agent
from app.agent.planner import Executor
from app.tools.builtin import Tool
from app.tools.registry import ToolRegistry


def test_agent_iterates_after_tool_execution() -> None:
    llm = Mock()
    llm.decide_tool.side_effect = [
        {
            "action": "tool",
            "tool_name": "calculator",
            "arguments": {"expression": "2 + 3"},
            "reason": "tool_required",
        },
        {
            "action": "final",
            "tool_name": None,
            "arguments": {},
            "reason": "no_tool_available",
        },
    ]
    llm.generate.return_value = "The result is 5."

    agent = Agent(llm=llm)

    result = agent.run("Calculate 2 + 3.")

    assert result.answer == "The result is 5."
    assert result.steps == 2
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]["tool"] == "calculator"
    assert result.tool_calls[0]["result"] == "5"
    assert llm.decide_tool.call_count == 2

    second_context = llm.decide_tool.call_args_list[1].kwargs["context"]
    assert "calculator" in second_context
    assert "5" in second_context


def test_agent_enforces_max_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agent.agent.settings.agent_max_steps",
        2,
    )

    llm = Mock()
    llm.decide_tool.return_value = {
        "action": "tool",
        "tool_name": "calculator",
        "arguments": {"expression": "1 + 1"},
        "reason": "tool_required",
    }

    agent = Agent(llm=llm)

    with pytest.raises(RuntimeError, match="Maximum agent-step limit reached"):
        agent.run("Keep calculating.")

    assert llm.decide_tool.call_count == 2


def test_agent_enforces_max_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agent.agent.settings.agent_max_steps",
        5,
    )
    monkeypatch.setattr(
        "app.agent.agent.settings.agent_max_tool_calls",
        1,
    )

    llm = Mock()
    llm.decide_tool.side_effect = [
        {
            "action": "tool",
            "tool_name": "calculator",
            "arguments": {"expression": "1 + 1"},
            "reason": "tool_required",
        },
        {
            "action": "tool",
            "tool_name": "calculator",
            "arguments": {"expression": "2 + 2"},
            "reason": "tool_required",
        },
    ]

    agent = Agent(llm=llm)

    with pytest.raises(RuntimeError, match="Maximum tool-call limit reached"):
        agent.run("Perform multiple calculations.")

    assert llm.decide_tool.call_count == 2


def test_executor_blocks_dangerous_tools_by_default() -> None:
    registry = ToolRegistry()
    dangerous_tool = Tool(
        name="dangerous_test",
        description="Test-only dangerous tool",
        function=lambda: "executed",
        dangerous=True,
    )
    registry.register(dangerous_tool)
    executor = Executor(registry)

    with pytest.raises(PermissionError, match="Dangerous tools are disabled"):
        executor.execute_tool("dangerous_test", {}, 0)


def test_system_prompt_treats_tool_results_as_untrusted() -> None:
    prompt = Agent()._system_prompt()

    assert "untrusted data" in prompt.lower()
    assert "instructions" in prompt.lower()


def test_executor_rejects_negative_tool_call_count() -> None:
    registry = ToolRegistry()
    tool = Tool(
        name="safe_test",
        description="Test-only safe tool",
        function=lambda: "executed",
    )
    registry.register(tool)
    executor = Executor(registry)

    with pytest.raises(ValueError, match="tool_calls_used"):
        executor.execute_tool("safe_test", {}, -1)


def test_executor_rejects_non_dictionary_arguments() -> None:
    executor = Executor(ToolRegistry())

    with pytest.raises(ValueError, match="arguments must be a dictionary"):
        executor.execute_tool("calculator", ["1 + 1"], 0)


def test_agent_rejects_non_dictionary_decision() -> None:
    llm = Mock()
    llm.decide_tool.return_value = ["tool", "calculator"]

    agent = Agent(llm=llm)

    with pytest.raises(ValueError, match="Decision must be a dictionary"):
        agent.run("Calculate 2 + 3.")


def test_agent_rejects_invalid_decision_action() -> None:
    llm = Mock()
    llm.decide_tool.return_value = {
        "action": "execute_anything",
        "tool_name": "calculator",
        "arguments": {"expression": "2 + 3"},
        "reason": "tool_required",
    }

    agent = Agent(llm=llm)

    with pytest.raises(ValueError, match="Invalid decision action"):
        agent.run("Calculate 2 + 3.")

    assert llm.generate.call_count == 0


@pytest.mark.parametrize(
    ("provider", "selected_client"),
    [
        ("ollama", "OllamaClient"),
        ("gemini", "GeminiClient"),
    ],
)
def test_agent_selects_configured_llm_provider(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    selected_client: str,
) -> None:
    import app.agent.agent as agent_module

    ollama = Mock(name="ollama_client")
    gemini = Mock(name="gemini_client")
    monkeypatch.setattr(agent_module.settings, "llm_provider", provider)
    monkeypatch.setattr(agent_module, "OllamaClient", Mock(return_value=ollama))
    monkeypatch.setattr(agent_module, "GeminiClient", Mock(return_value=gemini))

    agent = Agent()

    expected = ollama if selected_client == "OllamaClient" else gemini
    assert agent.llm is expected


def test_agent_rejects_unsupported_llm_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.agent.agent.settings.llm_provider",
        "unsupported-provider",
    )

    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        Agent()
