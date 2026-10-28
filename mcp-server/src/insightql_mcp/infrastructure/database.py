import json
from decimal import Decimal

import pandas as pd
from sqlalchemy import Connection, Engine, create_engine, inspect, text

from insightql_mcp.domain.errors import TableNotFound
from insightql_mcp.domain.models import (
    ColumnSchema,
    ForeignKey,
    QueryResult,
    TableSchema,
    TableSummary,
)

_SQLGLOT_DIALECTS = {"postgresql": "postgres", "mysql": "mysql"}


class SqlAlchemyDatabase:
    def __init__(self, url: str, timeout_ms: int = 5000) -> None:
        self._engine: Engine = create_engine(url, pool_pre_ping=True)
        self._timeout_ms = timeout_ms

    @property
    def dialect(self) -> str:
        name = self._engine.dialect.name
        return _SQLGLOT_DIALECTS.get(name, name)

    def list_tables(self) -> list[TableSummary]:
        inspector = inspect(self._engine)
        return [
            TableSummary(name=name, description=inspector.get_table_comment(name).get("text"))
            for name in sorted(inspector.get_table_names())
        ]

    def describe_table(self, name: str) -> TableSchema:
        inspector = inspect(self._engine)
        if name not in inspector.get_table_names():
            raise TableNotFound(f"A tabela '{name}' não existe.")
        columns = tuple(
            ColumnSchema(
                name=column["name"],
                type=str(column["type"]),
                nullable=bool(column["nullable"]),
                description=column.get("comment"),
            )
            for column in inspector.get_columns(name)
        )
        foreign_keys = tuple(
            ForeignKey(
                columns=tuple(fk["constrained_columns"]),
                referred_table=fk["referred_table"],
                referred_columns=tuple(fk["referred_columns"]),
            )
            for fk in inspector.get_foreign_keys(name)
        )
        return TableSchema(
            name=name,
            description=inspector.get_table_comment(name).get("text"),
            columns=columns,
            primary_key=tuple(inspector.get_pk_constraint(name)["constrained_columns"]),
            foreign_keys=foreign_keys,
        )

    def execute(self, sql: str, max_rows: int) -> QueryResult:
        with self._engine.connect() as connection:
            self._prepare_read_only(connection)
            cursor = connection.execute(text(sql))
            columns = tuple(cursor.keys())
            fetched = cursor.fetchmany(max_rows + 1)
        frame = pd.DataFrame(fetched, columns=list(columns)).head(max_rows)
        return QueryResult(
            columns=columns,
            rows=tuple(_to_records(frame)),
            truncated=len(fetched) > max_rows,
        )

    def _prepare_read_only(self, connection: Connection) -> None:
        if self.dialect == "postgres":
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            connection.exec_driver_sql(f"SET LOCAL statement_timeout = {int(self._timeout_ms)}")
        elif self.dialect == "mysql":
            connection.exec_driver_sql(f"SET SESSION max_execution_time = {int(self._timeout_ms)}")
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")


def _to_records(frame: pd.DataFrame) -> list[dict]:
    normalized = frame.map(lambda v: float(v) if isinstance(v, Decimal) else v)
    return json.loads(normalized.to_json(orient="records", date_format="iso", force_ascii=False))
