from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from insightql_mcp.domain.errors import QueryRejected

_WRITE_NODE_NAMES = (
    "Insert",
    "Update",
    "Delete",
    "Merge",
    "Drop",
    "Create",
    "Alter",
    "AlterTable",
    "TruncateTable",
    "Command",
    "Into",
    "Lock",
    "Grant",
)
_WRITE_NODES = tuple(getattr(exp, name) for name in _WRITE_NODE_NAMES if hasattr(exp, name))


@dataclass(frozen=True)
class QueryPolicy:
    max_rows: int = 500
    blocked_schemas: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"information_schema", "pg_catalog", "mysql", "performance_schema", "sys"}
        )
    )
    blocked_function_prefixes: tuple[str, ...] = ("pg_", "lo_", "dblink")
    blocked_functions: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"sleep", "benchmark", "load_file", "version", "current_version", "current_user"}
        )
    )


class SqlGuard:
    def __init__(self, dialect: str, policy: QueryPolicy | None = None) -> None:
        self._dialect = dialect
        self._policy = policy or QueryPolicy()

    def sanitize(self, sql: str) -> str:
        statement = self._parse_single(sql)
        self._ensure_read_only(statement)
        self._ensure_allowed_sources(statement)
        self._ensure_allowed_functions(statement)
        return self._enforce_limit(statement).sql(dialect=self._dialect)

    def _parse_single(self, sql: str) -> exp.Expression:
        if not sql or not sql.strip():
            raise QueryRejected("A consulta está vazia.")
        try:
            statements = [s for s in sqlglot.parse(sql, read=self._dialect) if s is not None]
        except ParseError as error:
            raise QueryRejected(f"SQL inválido: {error}") from error
        if len(statements) != 1:
            raise QueryRejected("Envie exatamente uma instrução SQL por vez.")
        return statements[0]

    def _ensure_read_only(self, statement: exp.Expression) -> None:
        if not isinstance(statement, exp.Query):
            raise QueryRejected("Somente consultas SELECT são permitidas.")
        if statement.find(*_WRITE_NODES):
            raise QueryRejected("A consulta contém operações de escrita ou DDL.")

    def _ensure_allowed_sources(self, statement: exp.Expression) -> None:
        for table in statement.find_all(exp.Table):
            schema = (table.db or "").lower()
            name = table.name.lower()
            if schema in self._policy.blocked_schemas or name.startswith("pg_"):
                raise QueryRejected(f"Acesso a '{table.sql()}' não é permitido.")

    def _ensure_allowed_functions(self, statement: exp.Expression) -> None:
        for function in statement.find_all(exp.Func):
            name = _function_name(function)
            if name in self._policy.blocked_functions or name.startswith(
                self._policy.blocked_function_prefixes
            ):
                raise QueryRejected(f"A função '{name}' não é permitida.")

    def _enforce_limit(self, statement: exp.Expression) -> exp.Expression:
        max_rows = self._policy.max_rows
        if isinstance(statement, exp.Select):
            current = _literal_limit(statement)
            if current is not None and current <= max_rows:
                return statement
            return statement.limit(max_rows)
        return exp.select("*").from_(statement.subquery("limited")).limit(max_rows)


def _function_name(function: exp.Func) -> str:
    if isinstance(function, exp.Anonymous):
        return str(function.name).lower()
    return function.sql_name().lower()


def _literal_limit(statement: exp.Select) -> int | None:
    limit = statement.args.get("limit")
    if limit is None:
        return None
    value = limit.expression
    if isinstance(value, exp.Literal) and value.is_int:
        return int(value.this)
    return None
