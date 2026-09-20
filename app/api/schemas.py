from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)


class ToolCallResponse(BaseModel):
    tool: str
    arguments: dict[str, Any]
    result: Any


class QueryResponse(BaseModel):
    answer: str
    tool_calls: list[ToolCallResponse]
    steps: int


class HealthResponse(BaseModel):
    status: str
    ollama: bool
    model: str
