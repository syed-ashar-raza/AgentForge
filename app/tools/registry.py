from typing import Any

from app.tools.builtin import Tool, get_builtin_tools


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {
            tool.name: tool for tool in get_builtin_tools()
        }

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ValueError(f"Unknown tool: {name}") from exc

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "dangerous": tool.dangerous,
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        return self.get(name).execute(arguments)
