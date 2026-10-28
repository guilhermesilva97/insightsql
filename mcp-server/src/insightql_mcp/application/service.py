from insightql_mcp.application.ports import QueryExecutor, SchemaCatalog
from insightql_mcp.domain.models import ExecutedQuery, TableSchema, TableSummary
from insightql_mcp.domain.sql_guard import QueryPolicy, SqlGuard


class InsightService:
    def __init__(
        self,
        catalog: SchemaCatalog,
        executor: QueryExecutor,
        policy: QueryPolicy | None = None,
    ) -> None:
        self._catalog = catalog
        self._executor = executor
        self._policy = policy or QueryPolicy()
        self._guard = SqlGuard(executor.dialect, self._policy)

    @property
    def dialect(self) -> str:
        return self._executor.dialect

    def list_tables(self) -> list[TableSummary]:
        return self._catalog.list_tables()

    def describe_table(self, name: str) -> TableSchema:
        return self._catalog.describe_table(name)

    def run_query(self, sql: str) -> ExecutedQuery:
        safe_sql = self._guard.sanitize(sql)
        result = self._executor.execute(safe_sql, self._policy.max_rows)
        return ExecutedQuery(sql=safe_sql, result=result)
