import pytest

from insightql_api.application.ask_question import AskQuestion
from insightql_api.domain.conversation import ModelTurn, ToolOutcome
from insightql_api.domain.events import AgentFailed, AnswerReady, ToolFinished, ToolStarted
from tests.fakes import FakeGateway, ScriptedModel, call


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def collect(use_case: AskQuestion, question: str = "Clientes por estado?") -> list:
    return [event async for event in use_case.run(question)]


@pytest.mark.anyio
async def test_runs_tools_and_presents_chart() -> None:
    gateway = FakeGateway()
    model = ScriptedModel(
        [
            ModelTurn(None, (call("list_tables"),)),
            ModelTurn(None, (call("run_query", "c2", sql="SELECT ..."),)),
            ModelTurn(
                None,
                (
                    call(
                        "present_answer",
                        "c3",
                        summary="SP e RJ empatam com 30 clientes.",
                        chart="bar",
                        x="state",
                        y=["total"],
                    ),
                ),
            ),
        ]
    )

    events = await collect(AskQuestion(model, gateway.factory()))

    assert [type(e) for e in events] == [
        ToolStarted,
        ToolFinished,
        ToolStarted,
        ToolFinished,
        AnswerReady,
    ]
    answer = events[-1]
    assert answer.summary == "SP e RJ empatam com 30 clientes."
    assert answer.chart.kind == "bar"
    assert answer.chart.y == ("total",)
    assert answer.query.rows[0] == {"state": "SP", "total": 30}
    assert gateway.calls == [("list_tables", {}), ("run_query", {"sql": "SELECT ..."})]


@pytest.mark.anyio
async def test_falls_back_to_table_when_chart_columns_do_not_exist() -> None:
    model = ScriptedModel(
        [
            ModelTurn(None, (call("run_query", sql="SELECT ..."),)),
            ModelTurn(
                None,
                (call("present_answer", "c2", summary="ok", chart="line", x="mes", y=["receita"]),),
            ),
        ]
    )

    events = await collect(AskQuestion(model, FakeGateway().factory()))

    assert events[-1].chart.kind == "table"


@pytest.mark.anyio
async def test_sends_tool_errors_back_to_the_model_for_self_correction() -> None:
    gateway = FakeGateway()
    gateway.responses["run_query"] = ToolOutcome(False, 'column "estado" does not exist')
    model = ScriptedModel(
        [
            ModelTurn(None, (call("run_query", sql="SELECT estado FROM customers"),)),
            ModelTurn("Não encontrei a coluna.", ()),
        ]
    )

    events = await collect(AskQuestion(model, gateway.factory()))

    finished = next(e for e in events if isinstance(e, ToolFinished))
    assert finished.ok is False
    tool_message = model.received[1][-1]
    assert tool_message.role == "tool"
    assert tool_message.content.startswith("ERRO:")
    assert isinstance(events[-1], AnswerReady)
    assert events[-1].query is None


@pytest.mark.anyio
async def test_stops_after_max_steps() -> None:
    model = ScriptedModel([ModelTurn(None, (call("list_tables"),)) for _ in range(3)])

    events = await collect(AskQuestion(model, FakeGateway().factory(), max_steps=3))

    assert isinstance(events[-1], AgentFailed)


@pytest.mark.anyio
async def test_system_prompt_includes_server_instructions() -> None:
    model = ScriptedModel([ModelTurn("Resposta direta.", ())])

    await collect(AskQuestion(model, FakeGateway().factory()))

    system = model.received[0][0]
    assert system.role == "system"
    assert "banco postgres" in system.content
