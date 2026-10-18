import sys
from pathlib import Path

import pytest

from app.tools.mcp_client import MCPToolClient
from app.tools.registry import ToolRegistry


@pytest.fixture
def mcp_client():
    project_root = Path(__file__).resolve().parents[1]
    registry = ToolRegistry()

    with MCPToolClient(
        registry,
        server_name="agentforge",
        command=sys.executable,
        args=["-m", "app.mcp_server"],
        cwd=str(project_root),
    ) as client:
        yield registry, client


def test_mcp_client_discovers_namespaced_tools(mcp_client):
    registry, _ = mcp_client
    names = {tool["name"] for tool in registry.list_tools()}

    assert "mcp__agentforge__calculator" in names
    assert "mcp__agentforge__current_datetime" in names


def test_mcp_client_executes_remote_calculator(mcp_client):
    registry, _ = mcp_client

    result = registry.execute(
        "mcp__agentforge__calculator",
        {"expression": "2 + 3 * 4"},
    )

    assert result == "14"


def test_mcp_client_executes_remote_datetime(mcp_client):
    registry, _ = mcp_client

    result = registry.execute("mcp__agentforge__current_datetime", {})

    assert isinstance(result, str)
    assert result.endswith("+00:00")


def test_mcp_client_propagates_remote_tool_errors(mcp_client):
    registry, _ = mcp_client

    with pytest.raises(RuntimeError, match="Invalid arithmetic expression"):
        registry.execute(
            "mcp__agentforge__calculator",
            {"expression": "1 / 0"},
        )
