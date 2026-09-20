import logging
from dataclasses import dataclass
from typing import Any

from app.agent.planner import Executor, Planner
from app.llm.client import OllamaClient
from app.memory.store import MemoryStore
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    answer: str
    tool_calls: list[dict[str, Any]]
    steps: int


class Agent:
    def __init__(
        self,
        llm: OllamaClient | None = None,
        tools: ToolRegistry | None = None,
        memory: MemoryStore | None = None,
    ) -> None:
        self.llm = llm or OllamaClient()
        self.tools = tools or ToolRegistry()
        self.memory = memory or MemoryStore("data/agentforge.db")
        self.planner = Planner()
        self.executor = Executor(self.tools)

    def _system_prompt(self) -> str:
        return """
You are AgentForge, a reliable AI agent.

You are concise, factual, and transparent.
Do not claim to have performed an action unless the execution result confirms it.
When tool results are provided, use them as authoritative execution results.
If the user's request does not require a tool, answer normally.
""".strip()

    def run(self, user_request: str) -> AgentResult:
        if not user_request.strip():
            raise ValueError("User request cannot be empty.")

        self.memory.add("user", user_request)
        plan = self.planner.create_plan(user_request, self.tools)

        tool_calls: list[dict[str, Any]] = []
        tool_calls_used = 0
        steps = 0

        decision = self.llm.decide_tool(
            user_request,
            self.tools.list_tools(),
        )
        steps += 1

        if decision.get("action") == "tool":
            tool_name = decision.get("tool_name")
            arguments = decision.get("arguments") or {}

            if not isinstance(tool_name, str):
                raise ValueError("Model selected a tool without a valid name.")

            result, tool_calls_used = self.executor.execute_tool(
                tool_name,
                arguments,
                tool_calls_used,
            )

            tool_calls.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                }
            )

            prompt = f"""
Original user request:
{user_request}

Plan:
{plan.steps}

Executed tool:
{tool_name}

Tool arguments:
{arguments}

Tool result:
{result}

Answer the user using the verified tool result.
Do not mention internal planning unless useful.
""".strip()

            answer = self.llm.generate(
                prompt,
                system=self._system_prompt(),
            )
        else:
            answer = self.llm.generate(
                user_request,
                system=self._system_prompt(),
            )

        self.memory.add("assistant", answer)

        return AgentResult(
            answer=answer,
            tool_calls=tool_calls,
            steps=steps,
        )
