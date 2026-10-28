from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TableSummary:
    name: str
    description: str | None


@dataclass(frozen=True)
class ColumnSchema:
    name: str
    type: str
    nullable: bool
    description: str | None


@dataclass(frozen=True)
class ForeignKey:
    columns: tuple[str, ...]
    referred_table: str
    referred_columns: tuple[str, ...]


@dataclass(frozen=True)
class TableSchema:
    name: str
    description: str | None
    columns: tuple[ColumnSchema, ...]
    primary_key: tuple[str, ...]
    foreign_keys: tuple[ForeignKey, ...] = ()


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    truncated: bool


@dataclass(frozen=True)
class ExecutedQuery:
    sql: str
    result: QueryResult
