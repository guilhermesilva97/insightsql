import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult, TextContent

from insightql_api.domain.conversation import ToolOutcome, ToolSpec


class McpToolGateway:
    def __init__(self, session: ClientSession, instructions: str) -> None:
        self._session = session
        self._instructions = instructions

    @property
    def instructions(self) -> str:
        return self._instructions

    async def list_tools(self) -> list[ToolSpec]:
        result = await self._session.list_tools()
        return [
            ToolSpec(
                name=tool.name,
                description=tool.description or "",
                parameters=tool.inputSchema,
            )
            for tool in result.tools
        ]

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolOutcome:
        result = await self._session.call_tool(name, arguments)
        return ToolOutcome(ok=not result.isError, content=_content_of(result))


@asynccontextmanager
async def open_mcp_gateway(url: str) -> AsyncIterator[McpToolGateway]:
    async with (
        streamablehttp_client(url) as (read, write, _),
        ClientSession(read, write) as session,
    ):
        initialized = await session.initialize()
        yield McpToolGateway(session, initialized.instructions or "")


def _content_of(result: CallToolResult) -> Any:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        if set(structured) == {"result"}:
            return structured["result"]
        return structured
    text = "\n".join(block.text for block in result.content if isinstance(block, TextContent))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text
