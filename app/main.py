import logging
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.responses import Response

from app.api.routes import agent, router
from app.core.config import settings
from app.tools.mcp_client import MCPToolClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    mcp_client = None
    application.state.mcp_client = None

    try:
        if settings.mcp_enabled:
            mcp_client = MCPToolClient(
                registry=agent.tools,
                server_name="agentforge",
                command=sys.executable,
                args=["-m", "app.mcp_server"],
                cwd=str(Path(__file__).resolve().parent.parent),
            )
            application.state.mcp_client = mcp_client

        yield
    finally:
        if mcp_client is not None:
            mcp_client.close()
            application.state.mcp_client = None


app = FastAPI(
    title="AgentForge",
    description="Production-oriented local AI agent platform.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def observe_requests(request: Request, call_next) -> Response:
    request_id = str(uuid4())
    request.state.request_id = request_id
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - started_at) * 1000
        route = getattr(request.scope.get("route"), "path", request.url.path)
        logger.exception(
            "http_request_failed method=%s route=%s status_code=500 duration_ms=%.2f request_id=%s",
            request.method,
            route,
            duration_ms,
            request_id,
        )
        return Response(
            content="Internal Server Error",
            status_code=500,
            headers={"X-Request-ID": request_id},
        )

    duration_ms = (time.perf_counter() - started_at) * 1000
    route = getattr(request.scope.get("route"), "path", request.url.path)
    response.headers["X-Request-ID"] = request_id

    logger.info(
        "http_request_completed method=%s route=%s status_code=%s duration_ms=%.2f request_id=%s",
        request.method,
        route,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "AgentForge",
        "version": "0.1.0",
        "status": "running",
    }
