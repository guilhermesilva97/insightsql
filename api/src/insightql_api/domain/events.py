from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ChartKind = Literal["bar", "line", "pie", "table"]


@dataclass(frozen=True)
class ChartSpec:
    kind: ChartKind
    x: str | None = None
    y: tuple[str, ...] = ()
    title: str | None = None


@dataclass(frozen=True)
class QuerySnapshot:
    sql: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    truncated: bool


@dataclass(frozen=True)
class AgentEvent:
    type: str = field(init=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolStarted(AgentEvent):
    call_id: str
    tool: str
    arguments: dict[str, Any]
    type: str = field(default="tool_started", init=False)


@dataclass(frozen=True)
class ToolFinished(AgentEvent):
    call_id: str
    tool: str
    ok: bool
    summary: str
    type: str = field(default="tool_finished", init=False)


@dataclass(frozen=True)
class AnswerReady(AgentEvent):
    summary: str
    chart: ChartSpec
    query: QuerySnapshot | None
    type: str = field(default="answer", init=False)


@dataclass(frozen=True)
class AgentFailed(AgentEvent):
    message: str
    type: str = field(default="error", init=False)
