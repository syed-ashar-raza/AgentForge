from unittest.mock import Mock

import pytest

from app.agent.agent import Agent


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
