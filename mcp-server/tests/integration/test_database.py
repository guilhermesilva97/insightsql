import os

import pytest
from sqlalchemy.exc import DBAPIError

from insightql_mcp.domain.errors import TableNotFound
from insightql_mcp.infrastructure.database import SqlAlchemyDatabase

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="DATABASE_URL não definido"),
]


@pytest.fixture(scope="module")
def database() -> SqlAlchemyDatabase:
    return SqlAlchemyDatabase(os.environ["DATABASE_URL"], timeout_ms=2000)


def test_lists_seeded_tables_with_descriptions(database: SqlAlchemyDatabase) -> None:
    tables = {t.name: t.description for t in database.list_tables()}
    assert set(tables) == {"categories", "products", "customers", "orders", "order_items"}
    assert tables["orders"]


def test_describes_foreign_keys(database: SqlAlchemyDatabase) -> None:
    schema = database.describe_table("order_items")
    assert {fk.referred_table for fk in schema.foreign_keys} == {"orders", "products"}


def test_unknown_table_raises(database: SqlAlchemyDatabase) -> None:
    with pytest.raises(TableNotFound):
        database.describe_table("salaries")


def test_executes_query_and_serializes_decimals(database: SqlAlchemyDatabase) -> None:
    result = database.execute("SELECT name, unit_price FROM products ORDER BY id", max_rows=3)
    assert result.columns == ("name", "unit_price")
    assert len(result.rows) == 3
    assert result.truncated is True
    assert isinstance(result.rows[0]["unit_price"], float)


def test_database_user_cannot_write_even_without_guard(database: SqlAlchemyDatabase) -> None:
    with pytest.raises(DBAPIError):
        database.execute("DELETE FROM order_items", max_rows=1)
