from fastapi import APIRouter, HTTPException

from app.agent.agent import Agent
from app.api.schemas import HealthResponse, QueryRequest, QueryResponse
from app.core.config import settings

router = APIRouter(prefix="/api/v1")
agent = Agent()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    ollama_ok = agent.llm.health()
    return HealthResponse(
        status="ok" if ollama_ok else "degraded",
        ollama=ollama_ok,
        model=settings.ollama_model,
    )


@router.get("/tools")
def tools() -> dict:
    return {"tools": agent.tools.list_tools()}


@router.get("/memory")
def memory() -> dict:
    return {"messages": agent.memory.recent()}


@router.delete("/memory")
def clear_memory() -> dict:
    agent.memory.clear()
    return {"status": "cleared"}


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    try:
        result = agent.run(request.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return QueryResponse(
        answer=result.answer,
        tool_calls=result.tool_calls,
        steps=result.steps,
    )
