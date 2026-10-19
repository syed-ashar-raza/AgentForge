from dataclasses import dataclass
from typing import Any

from app.tools.registry import ToolRegistry


@dataclass
class Plan:
    goal: str
    steps: list[str]


class Planner:
    def create_plan(self, goal: str, tools: ToolRegistry) -> Plan:
        steps = [
            "Understand the user's objective.",
            "Determine whether a registered tool is required.",
            "Execute the minimum necessary actions.",
            "Produce a concise result grounded in the execution results.",
        ]
        return Plan(goal=goal, steps=steps)


class Executor:
    def __init__(self, tools: ToolRegistry, max_tool_calls: int = 5) -> None:
        self.tools = tools
        self.max_tool_calls = max_tool_calls

    def execute_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        tool_calls_used: int,
    ) -> tuple[Any, int]:
        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a dictionary.")

        if tool_calls_used < 0:
            raise ValueError("tool_calls_used cannot be negative.")

        if tool_calls_used >= self.max_tool_calls:
            raise RuntimeError("Maximum tool-call limit reached.")

        tool = self.tools.get(name)
        if tool.dangerous:
            raise PermissionError("Dangerous tools are disabled by default.")

        result = tool.execute(arguments)
        return result, tool_calls_used + 1
