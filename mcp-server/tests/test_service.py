from dataclasses import dataclass, field

import pytest

from insightql_mcp.application.service import InsightService
from insightql_mcp.domain.errors import QueryRejected
from insightql_mcp.domain.models import QueryResult, TableSchema, TableSummary
from insightql_mcp.domain.sql_guard import QueryPolicy


@dataclass
class FakeDatabase:
    executed: list[tuple[str, int]] = field(default_factory=list)

    @property
    def dialect(self) -> str:
        return "postgres"

    def list_tables(self) -> list[TableSummary]:
        return [TableSummary("orders", "Pedidos")]

    def describe_table(self, name: str) -> TableSchema:
        return TableSchema(name=name, description=None, columns=(), primary_key=("id",))

    def execute(self, sql: str, max_rows: int) -> QueryResult:
        self.executed.append((sql, max_rows))
        return QueryResult(columns=("total",), rows=({"total": 3},), truncated=False)


def test_run_query_executes_sanitized_sql() -> None:
    database = FakeDatabase()
    service = InsightService(database, database, QueryPolicy(max_rows=20))

    executed = service.run_query("SELECT COUNT(*) AS total FROM orders")

    assert executed.sql == "SELECT COUNT(*) AS total FROM orders LIMIT 20"
    assert database.executed == [(executed.sql, 20)]
    assert executed.result.rows == ({"total": 3},)


def test_run_query_never_reaches_database_when_rejected() -> None:
    database = FakeDatabase()
    service = InsightService(database, database)

    with pytest.raises(QueryRejected):
        service.run_query("DELETE FROM orders")

    assert database.executed == []
