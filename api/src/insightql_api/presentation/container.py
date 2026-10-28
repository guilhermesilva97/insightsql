from functools import partial

from openai import AsyncOpenAI

from insightql_api.application.ask_question import AskQuestion
from insightql_api.config import Settings
from insightql_api.infrastructure.mcp_gateway import open_mcp_gateway
from insightql_api.infrastructure.openai_model import OpenAICompatibleModel


def build_ask_question(settings: Settings) -> AskQuestion:
    client = AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        timeout=settings.llm_timeout_seconds,
    )
    return AskQuestion(
        model=OpenAICompatibleModel(
            client,
            settings.llm_model,
            temperature=settings.llm_temperature,
            reasoning_effort=settings.llm_reasoning_effort,
        ),
        gateway_factory=partial(open_mcp_gateway, settings.mcp_server_url),
        max_steps=settings.agent_max_steps,
    )
