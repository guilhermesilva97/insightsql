from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from insightql_api.domain.conversation import Message, ModelTurn, ToolCall, ToolOutcome, ToolSpec

QUERY_RESULT = {
    "sql": "SELECT state, COUNT(*) AS total FROM customers GROUP BY state LIMIT 500",
    "columns": ["state", "total"],
    "rows": [{"state": "SP", "total": 30}, {"state": "RJ", "total": 30}],
    "row_count": 2,
    "truncated": False,
}


def call(name: str, call_id: str = "c1", **arguments: Any) -> ToolCall:
    return ToolCall(id=call_id, name=name, arguments=arguments)


@dataclass
class ScriptedModel:
    turns: list[ModelTurn]
    received: list[list[Message]] = field(default_factory=list)

    async def complete(self, messages: Sequence[Message], tools: Sequence[ToolSpec]) -> ModelTurn:
        self.received.append(list(messages))
        return self.turns.pop(0)


@dataclass
class FakeGateway:
    responses: dict[str, ToolOutcome] = field(
        default_factory=lambda: {
            "list_tables": ToolOutcome(True, {"tables": [{"name": "customers"}]}),
            "run_query": ToolOutcome(True, QUERY_RESULT),
        }
    )
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    @property
    def instructions(self) -> str:
        return "banco postgres"

    async def list_tools(self) -> list[ToolSpec]:
        return [ToolSpec(name, "", {"type": "object"}) for name in self.responses]

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolOutcome:
        self.calls.append((name, arguments))
        return self.responses[name]

    def factory(self):
        @asynccontextmanager
        async def open_gateway() -> AsyncIterator["FakeGateway"]:
            yield self

        return open_gateway
