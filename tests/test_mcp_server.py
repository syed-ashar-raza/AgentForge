import asyncio

from app.mcp_server import mcp


def test_mcp_server_registers_expected_tools() -> None:
    tools = {tool.name for tool in mcp._tool_manager.list_tools()}
    assert tools == {"calculator", "current_datetime"}


def test_mcp_calculator_tool_executes() -> None:
    async def run_tool() -> str:
        tool = mcp._tool_manager.get_tool("calculator")
        return await tool.run({"expression": "2 + 3 * 4"})

    assert asyncio.run(run_tool()) == "14"


def test_mcp_datetime_tool_returns_utc_timestamp() -> None:
    async def run_tool() -> str:
        tool = mcp._tool_manager.get_tool("current_datetime")
        return await tool.run({})

    assert asyncio.run(run_tool()).endswith("+00:00")
