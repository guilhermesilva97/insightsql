import json

from fastapi.testclient import TestClient

from insightql_api.application.ask_question import AskQuestion
from insightql_api.domain.conversation import ModelTurn
from insightql_api.presentation.app import create_app
from tests.fakes import FakeGateway, ScriptedModel, call


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def test_streams_agent_events_as_sse() -> None:
    model = ScriptedModel(
        [
            ModelTurn(None, (call("run_query", sql="SELECT ..."),)),
            ModelTurn(
                None,
                (call("present_answer", "c2", summary="ok", chart="pie", x="state", y=["total"]),),
            ),
        ]
    )
    client = TestClient(create_app(AskQuestion(model, FakeGateway().factory())))

    response = client.post("/api/questions", json={"question": "Clientes por estado?"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    assert [name for name, _ in events] == ["tool_started", "tool_finished", "answer"]
    assert events[-1][1]["chart"]["kind"] == "pie"


def test_streams_error_event_when_infrastructure_fails() -> None:
    class BrokenModel:
        async def complete(self, messages, tools):
            raise ConnectionError("llm offline")

    client = TestClient(create_app(AskQuestion(BrokenModel(), FakeGateway().factory())))

    response = client.post("/api/questions", json={"question": "Clientes por estado?"})

    assert parse_sse(response.text)[-1][0] == "error"


def test_validates_question_length() -> None:
    model = ScriptedModel([])
    client = TestClient(create_app(AskQuestion(model, FakeGateway().factory())))

    assert client.post("/api/questions", json={"question": "?"}).status_code == 422
