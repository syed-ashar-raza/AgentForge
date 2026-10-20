import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.routes import agent, router
from app.core.config import settings
from app.tools.mcp_client import MCPToolClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


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

app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "AgentForge",
        "version": "0.1.0",
        "status": "running",
    }
