from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol

from insightql_api.domain.conversation import Message, ModelTurn, ToolOutcome, ToolSpec


class LanguageModel(Protocol):
    async def complete(
        self, messages: Sequence[Message], tools: Sequence[ToolSpec]
    ) -> ModelTurn: ...


class ToolGateway(Protocol):
    @property
    def instructions(self) -> str: ...

    async def list_tools(self) -> list[ToolSpec]: ...

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolOutcome: ...


class ToolGatewayFactory(Protocol):
    def __call__(self) -> AbstractAsyncContextManager[ToolGateway]: ...
