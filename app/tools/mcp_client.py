import asyncio
import concurrent.futures
import logging
import threading
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.tools.builtin import Tool
from app.tools.registry import ToolRegistry


class MCPToolClient:
    """Register and invoke tools from a persistent MCP stdio server."""

    def __init__(
        self,
        registry: ToolRegistry,
        server_name: str,
        command: str,
        args: list[str] | None = None,
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        if not server_name or not server_name.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Invalid MCP server name.")

        self.server_name = server_name
        self._server = StdioServerParameters(
            command=command,
            args=args or [],
            cwd=cwd,
            env=env,
        )

        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._requests: asyncio.Queue = asyncio.Queue()
        self._startup: concurrent.futures.Future[list[Any]] = concurrent.futures.Future()
        self._session: ClientSession | None = None
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"mcp-{server_name}",
            daemon=True,
        )
        self._serve_future: concurrent.futures.Future[Any] | None = None

        self._thread.start()

        if not self._ready.wait(10):
            self.close()
            raise TimeoutError("MCP event loop failed to start.")

        self._serve_future = asyncio.run_coroutine_threadsafe(
            self._serve(),
            self._loop,
        )

        try:
            tools = self._startup.result(timeout=30)

            for tool in tools:
                registry.register(
                    Tool(
                        name=f"mcp__{server_name}__{tool.name}",
                        description=(f"[MCP: {server_name}] {tool.description or tool.name}"),
                        function=self._invoker(tool.name),
                    )
                )
        except Exception:
            self.close()
            raise

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._ready.set()

        try:
            self._loop.run_forever()
        finally:
            self._loop.close()

    async def _serve(self) -> None:
        """Own the MCP connection and its lifecycle in one asyncio task."""
        try:
            async with AsyncExitStack() as stack:
                read_stream, write_stream = await stack.enter_async_context(
                    stdio_client(self._server)
                )

                session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
                self._session = session

                await session.initialize()
                tools = (await session.list_tools()).tools
                self._startup.set_result(tools)

                while True:
                    request = await self._requests.get()

                    if request is None:
                        break

                    name, arguments, future = request

                    try:
                        result = await self._call(session, name, arguments)
                        if not future.done():
                            future.set_result(result)
                    except Exception as exc:
                        if not future.done():
                            future.set_exception(exc)

        except Exception as exc:
            if not self._startup.done():
                self._startup.set_exception(exc)
            raise
        finally:
            self._session = None

    def _invoker(self, remote_name: str):
        def invoke(**arguments: Any) -> Any:
            if self._serve_future is None or self._serve_future.done():
                raise RuntimeError(f"MCP server '{self.server_name}' is disconnected.")

            result_future: concurrent.futures.Future[Any] = concurrent.futures.Future()

            asyncio.run_coroutine_threadsafe(
                self._requests.put((remote_name, arguments, result_future)),
                self._loop,
            ).result(timeout=10)

            return result_future.result(timeout=60)

        return invoke

    async def _call(
        self,
        session: ClientSession,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        result = await session.call_tool(name, arguments)

        if result.isError:
            message = "; ".join(item.text for item in result.content if hasattr(item, "text"))
            raise RuntimeError(message or f"MCP tool '{name}' failed.")

        if result.structuredContent is not None:
            content = result.structuredContent

            # Normalize simple MCP results such as {"result": "14"}.
            if isinstance(content, dict) and set(content) == {"result"}:
                return content["result"]

            return content

        if all(hasattr(item, "text") for item in result.content):
            return "\n".join(item.text for item in result.content)

        return [item.model_dump(mode="json") for item in result.content]

    def close(self) -> None:
        if not self._thread.is_alive():
            return

        try:
            if self._loop.is_running():
                if self._serve_future is not None and not self._serve_future.done():
                    asyncio.run_coroutine_threadsafe(
                        self._requests.put(None),
                        self._loop,
                    ).result(timeout=10)

                    try:
                        self._serve_future.result(timeout=10)
                    except Exception:
                        logging.getLogger(__name__).debug(
                            "MCP server exited with an error during shutdown",
                            exc_info=True,
                        )
        finally:
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)

            self._thread.join(timeout=10)

    def __enter__(self) -> MCPToolClient:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
