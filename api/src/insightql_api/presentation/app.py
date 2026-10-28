import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from insightql_api.application.ask_question import AskQuestion
from insightql_api.config import Settings
from insightql_api.domain.events import AgentEvent, AgentFailed
from insightql_api.presentation.container import build_ask_question

logger = logging.getLogger("insightql.api")


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


def create_app(ask_question: AskQuestion | None = None) -> FastAPI:
    use_case = ask_question or build_ask_question(Settings())
    app = FastAPI(title="InsightQL API", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/questions")
    async def ask(request: QuestionRequest) -> StreamingResponse:
        return StreamingResponse(
            _stream(use_case, request.question),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


async def _stream(use_case: AskQuestion, question: str) -> AsyncIterator[str]:
    queue: asyncio.Queue[AgentEvent | None] = asyncio.Queue()
    producer = asyncio.create_task(_produce(use_case, question, queue))
    try:
        while (event := await queue.get()) is not None:
            yield _sse(event)
    finally:
        producer.cancel()


async def _produce(
    use_case: AskQuestion, question: str, queue: asyncio.Queue[AgentEvent | None]
) -> None:
    try:
        async for event in use_case.run(question):
            await queue.put(event)
    except Exception:
        logger.exception("Falha ao processar a pergunta")
        await queue.put(AgentFailed("Erro interno ao falar com o modelo ou com o servidor MCP."))
    finally:
        await queue.put(None)


def _sse(event: AgentEvent) -> str:
    payload = json.dumps(event.to_dict(), ensure_ascii=False, default=str)
    return f"event: {event.type}\ndata: {payload}\n\n"
