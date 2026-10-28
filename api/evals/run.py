import asyncio
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from insightql_api.config import Settings
from insightql_api.domain.events import AnswerReady
from insightql_api.infrastructure.mcp_gateway import open_mcp_gateway
from insightql_api.presentation.container import build_ask_question

GOLDEN = Path(__file__).with_name("golden.json")


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    passed: bool
    detail: str


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def numeric_columns(rows: list[dict[str, Any]]) -> list[tuple[float, ...]]:
    if not rows:
        return []
    columns = []
    for name in rows[0]:
        values = [row.get(name) for row in rows]
        if all(_is_number(v) for v in values):
            columns.append(tuple(sorted(round(float(v), 2) for v in values)))
    return columns


def results_match(actual: list[dict[str, Any]], expected: list[dict[str, Any]]) -> bool:
    if len(actual) != len(expected):
        return False
    available = Counter(numeric_columns(actual))
    for column in numeric_columns(expected):
        if available[column] == 0:
            return False
        available[column] -= 1
    return True


async def evaluate(case: dict[str, Any], settings: Settings) -> EvalResult:
    async with open_mcp_gateway(settings.mcp_server_url) as gateway:
        expected = await gateway.call("run_query", {"sql": case["expected_sql"]})
    if not expected.ok:
        return EvalResult(case["id"], False, f"SQL de referência falhou: {expected.content}")

    answer = None
    async for event in build_ask_question(settings).run(case["question"]):
        if isinstance(event, AnswerReady):
            answer = event
    if answer is None or answer.query is None:
        return EvalResult(case["id"], False, "o agente não executou nenhuma consulta")

    passed = results_match(list(answer.query.rows), expected.content["rows"])
    return EvalResult(case["id"], passed, answer.query.sql)


async def main() -> int:
    settings = Settings()
    threshold = float(os.environ.get("EVALS_MIN_ACCURACY", "0.75"))
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))
    results = [await evaluate(case, settings) for case in cases]

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.case_id}: {result.detail}")
    accuracy = sum(r.passed for r in results) / len(results)
    print(f"\nAcurácia: {accuracy:.0%} (mínimo exigido: {threshold:.0%})")
    return 0 if accuracy >= threshold else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
