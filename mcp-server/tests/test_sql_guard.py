import pytest

from insightql_mcp.domain.errors import QueryRejected
from insightql_mcp.domain.sql_guard import QueryPolicy, SqlGuard


@pytest.fixture
def guard() -> SqlGuard:
    return SqlGuard("postgres", QueryPolicy(max_rows=100))


def test_adds_limit_when_missing(guard: SqlGuard) -> None:
    assert guard.sanitize("SELECT id FROM orders") == "SELECT id FROM orders LIMIT 100"


def test_keeps_smaller_limit(guard: SqlGuard) -> None:
    assert guard.sanitize("SELECT id FROM orders LIMIT 10").endswith("LIMIT 10")


def test_caps_larger_limit(guard: SqlGuard) -> None:
    assert guard.sanitize("SELECT id FROM orders LIMIT 5000").endswith("LIMIT 100")


def test_wraps_set_operations_to_enforce_limit(guard: SqlGuard) -> None:
    sql = guard.sanitize("SELECT id FROM orders UNION SELECT id FROM customers")
    assert sql.startswith("SELECT * FROM (")
    assert sql.endswith("LIMIT 100")


def test_accepts_cte_and_aggregations(guard: SqlGuard) -> None:
    sql = guard.sanitize(
        "WITH revenue AS (SELECT order_id, SUM(quantity * unit_price) AS total "
        "FROM order_items GROUP BY order_id) SELECT AVG(total) FROM revenue"
    )
    assert "LIMIT 100" in sql


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM orders",
        "UPDATE orders SET status = 'paid'",
        "INSERT INTO categories (name) VALUES ('x')",
        "DROP TABLE orders",
        "CREATE TABLE x (id INT)",
        "TRUNCATE TABLE orders",
        "SELECT * INTO backup FROM orders",
        "GRANT ALL ON orders TO public",
    ],
)
def test_rejects_write_operations(guard: SqlGuard, sql: str) -> None:
    with pytest.raises(QueryRejected):
        guard.sanitize(sql)


def test_rejects_multiple_statements(guard: SqlGuard) -> None:
    with pytest.raises(QueryRejected, match="exatamente uma"):
        guard.sanitize("SELECT 1; DELETE FROM orders")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM pg_catalog.pg_roles",
        "SELECT * FROM pg_shadow",
    ],
)
def test_rejects_system_catalogs(guard: SqlGuard, sql: str) -> None:
    with pytest.raises(QueryRejected, match="não é permitido"):
        guard.sanitize(sql)


@pytest.mark.parametrize(
    "sql",
    ["SELECT pg_sleep(10)", "SELECT pg_read_file('/etc/passwd')", "SELECT version()"],
)
def test_rejects_dangerous_functions(guard: SqlGuard, sql: str) -> None:
    with pytest.raises(QueryRejected, match="função"):
        guard.sanitize(sql)


@pytest.mark.parametrize("sql", ["", "   ", "SELEC id FRM orders"])
def test_rejects_empty_or_invalid_sql(guard: SqlGuard, sql: str) -> None:
    with pytest.raises(QueryRejected):
        guard.sanitize(sql)


def test_mysql_dialect_is_respected() -> None:
    guard = SqlGuard("mysql", QueryPolicy(max_rows=50))
    sql = guard.sanitize("SELECT DATE_FORMAT(ordered_at, '%Y-%m') AS month FROM orders")
    assert "DATE_FORMAT" in sql
    assert sql.endswith("LIMIT 50")
