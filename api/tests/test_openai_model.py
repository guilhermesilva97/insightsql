from types import SimpleNamespace

import pytest

from insightql_api.domain.conversation import Message
from insightql_api.infrastructure.openai_model import OpenAICompatibleModel


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class RecordingCompletions:
    def __init__(self) -> None:
        self.kwargs: dict = {}

    async def create(self, **kwargs):
        self.kwargs = kwargs
        message = SimpleNamespace(content="ok", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def client_with(completions: RecordingCompletions):
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


@pytest.mark.anyio
async def test_omits_optional_parameters_by_default() -> None:
    completions = RecordingCompletions()
    model = OpenAICompatibleModel(client_with(completions), "gpt-5.6-luna")

    await model.complete([Message.user("oi")], [])

    assert "temperature" not in completions.kwargs
    assert "reasoning_effort" not in completions.kwargs


@pytest.mark.anyio
async def test_sends_temperature_and_reasoning_effort_when_configured() -> None:
    completions = RecordingCompletions()
    model = OpenAICompatibleModel(
        client_with(completions), "modelo", temperature=0, reasoning_effort="low"
    )

    await model.complete([Message.user("oi")], [])

    assert completions.kwargs["temperature"] == 0
    assert completions.kwargs["reasoning_effort"] == "low"
