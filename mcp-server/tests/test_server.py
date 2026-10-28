import json

import pytest

from insightql_mcp.application.service import InsightService
from insightql_mcp.config import Settings
from insightql_mcp.presentation.server import build_server
from tests.test_service import FakeDatabase


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def server():
    database = FakeDatabase()
    settings = Settings(database_url="sqlite://", max_rows=20)
    return build_server(settings, InsightService(database, database))


@pytest.mark.anyio
async def test_exposes_the_three_tools(server) -> None:
    tools = {tool.name for tool in await server.list_tools()}
    assert tools == {"list_tables", "describe_table", "run_query"}


@pytest.mark.anyio
async def test_run_query_returns_sanitized_sql_and_rows(server) -> None:
    result = await server.call_tool("run_query", {"sql": "SELECT COUNT(*) AS total FROM orders"})
    blocks = result[0] if isinstance(result, tuple) else result
    payload = json.loads(blocks[0].text)
    assert payload["sql"].endswith("LIMIT 500")
    assert payload["rows"] == [{"total": 3}]
