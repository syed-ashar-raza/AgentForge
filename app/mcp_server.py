from mcp.server.fastmcp import FastMCP

from app.tools.registry import ToolRegistry

mcp = FastMCP(
    "AgentForge",
    instructions=(
        "AgentForge local tools. Use calculator for arithmetic "
        "and current_datetime for the current UTC time."
    ),
)

registry = ToolRegistry()


@mcp.tool()
def calculator(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    return registry.execute("calculator", {"expression": expression})


@mcp.tool()
def current_datetime() -> str:
    """Return the current UTC date and time in ISO 8601 format."""
    return registry.execute("current_datetime", {})


if __name__ == "__main__":
    mcp.run(transport="stdio")
