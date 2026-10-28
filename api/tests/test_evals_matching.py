from evals.run import results_match

EXPECTED = [{"name": "Notebook", "revenue": 3548454.0}, {"name": "Bicicleta", "revenue": 1309854.0}]


def test_accepts_renamed_columns_and_different_order() -> None:
    actual = [
        {"produto": "Bicicleta", "receita": 1309854},
        {"produto": "Notebook", "receita": 3548454},
    ]
    assert results_match(actual, EXPECTED)


def test_accepts_extra_numeric_columns() -> None:
    actual = [
        {"id": 1, "produto": "Notebook", "receita": 3548454.0, "unidades": 546},
        {"id": 10, "produto": "Bicicleta", "receita": 1309854.0, "unidades": 546},
    ]
    assert results_match(actual, EXPECTED)


def test_ignores_label_formats() -> None:
    expected = [{"month": "2025-01-01T00:00:00", "total": 145}]
    actual = [{"mes": "2025-01", "pedidos": 145}]
    assert results_match(actual, expected)


def test_rejects_wrong_values() -> None:
    actual = [
        {"produto": "Notebook", "receita": 3000000.0},
        {"produto": "Bicicleta", "receita": 1.0},
    ]
    assert not results_match(actual, EXPECTED)


def test_rejects_different_row_count() -> None:
    assert not results_match([{"receita": 3548454.0}], EXPECTED)
