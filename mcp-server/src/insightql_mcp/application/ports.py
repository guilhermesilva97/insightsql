from typing import Protocol

from insightql_mcp.domain.models import QueryResult, TableSchema, TableSummary


class SchemaCatalog(Protocol):
    def list_tables(self) -> list[TableSummary]: ...

    def describe_table(self, name: str) -> TableSchema: ...


class QueryExecutor(Protocol):
    @property
    def dialect(self) -> str: ...

    def execute(self, sql: str, max_rows: int) -> QueryResult: ...
