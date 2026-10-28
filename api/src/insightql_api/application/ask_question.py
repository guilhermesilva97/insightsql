import json
from collections.abc import AsyncIterator
from typing import Any

from insightql_api.application.ports import LanguageModel, ToolGateway, ToolGatewayFactory
from insightql_api.domain.conversation import Message, ToolCall, ToolOutcome, ToolSpec
from insightql_api.domain.events import (
    AgentEvent,
    AgentFailed,
    AnswerReady,
    ChartSpec,
    QuerySnapshot,
    ToolFinished,
    ToolStarted,
)

QUERY_TOOL = "run_query"
MODEL_PREVIEW_ROWS = 30

SYSTEM_PROMPT = """Você é o InsightQL, um analista de dados que responde perguntas de negócio \
consultando um banco relacional por meio de ferramentas.

Regras:
1. Nunca invente tabelas ou colunas: descubra o schema com as ferramentas antes de escrever SQL.
2. Execute a consulta com run_query. Se ela falhar, leia o erro, corrija o SQL e tente de novo.
3. As descrições das colunas trazem regras de negócio padrão. Aplique-as quando a pergunta \
não disser nada a respeito, mas o que o usuário pedir explicitamente prevalece \
(ex.: "considerando todos os pedidos" inclui os cancelados).
4. Responda sempre em português do Brasil, de forma objetiva e citando os números encontrados.
5. Para encerrar, chame present_answer com o resumo e a melhor visualização para o resultado.

Contexto do servidor de dados:
{instructions}"""

PRESENT_ANSWER = ToolSpec(
    name="present_answer",
    description=(
        "Encerra a análise. Informe o resumo em português e como o resultado da última "
        "consulta deve ser exibido."
    ),
    parameters={
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "Resposta final para o usuário."},
            "chart": {
                "type": "string",
                "enum": ["bar", "line", "pie", "table"],
                "description": (
                    "line para séries temporais, pie para proporções, bar para rankings."
                ),
            },
            "x": {"type": "string", "description": "Coluna do eixo X ou das categorias."},
            "y": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Colunas numéricas a serem plotadas.",
            },
            "title": {"type": "string"},
        },
        "required": ["summary", "chart"],
    },
)


class AskQuestion:
    def __init__(
        self,
        model: LanguageModel,
        gateway_factory: ToolGatewayFactory,
        max_steps: int = 8,
    ) -> None:
        self._model = model
        self._gateway_factory = gateway_factory
        self._max_steps = max_steps

    async def run(self, question: str) -> AsyncIterator[AgentEvent]:
        async with self._gateway_factory() as gateway:
            async for event in self._loop(question, gateway):
                yield event

    async def _loop(self, question: str, gateway: ToolGateway) -> AsyncIterator[AgentEvent]:
        tools = [*await gateway.list_tools(), PRESENT_ANSWER]
        messages = [
            Message.system(SYSTEM_PROMPT.format(instructions=gateway.instructions)),
            Message.user(question),
        ]
        last_query: QuerySnapshot | None = None

        for _ in range(self._max_steps):
            turn = await self._model.complete(messages, tools)
            messages.append(Message.assistant(turn))

            if not turn.tool_calls:
                yield AnswerReady(turn.text or "", _chart_for(last_query, {}), last_query)
                return

            for call in turn.tool_calls:
                if call.name == PRESENT_ANSWER.name:
                    summary = str(call.arguments.get("summary") or turn.text or "")
                    yield AnswerReady(summary, _chart_for(last_query, call.arguments), last_query)
                    return

                yield ToolStarted(call.id, call.name, call.arguments)
                outcome = await gateway.call(call.name, call.arguments)
                if outcome.ok and call.name == QUERY_TOOL:
                    last_query = _snapshot(outcome.content)
                yield ToolFinished(call.id, call.name, outcome.ok, _summarize(call, outcome))
                messages.append(Message.tool(call.id, _for_model(call.name, outcome)))

        yield AgentFailed(
            "Não consegui chegar a uma resposta dentro do limite de passos. "
            "Tente reformular a pergunta."
        )


def _snapshot(content: Any) -> QuerySnapshot | None:
    if not isinstance(content, dict) or "rows" not in content:
        return None
    return QuerySnapshot(
        sql=str(content.get("sql", "")),
        columns=tuple(content.get("columns", ())),
        rows=tuple(content.get("rows", ())),
        truncated=bool(content.get("truncated", False)),
    )


def _chart_for(query: QuerySnapshot | None, arguments: dict[str, Any]) -> ChartSpec:
    title = arguments.get("title")
    if query is None or not query.rows:
        return ChartSpec(kind="table", title=title)
    kind = arguments.get("chart", "table")
    x = arguments.get("x")
    y = tuple(column for column in arguments.get("y") or () if column in query.columns)
    if kind not in ("bar", "line", "pie") or x not in query.columns or not y:
        return ChartSpec(kind="table", title=title)
    if kind == "pie":
        y = y[:1]
    return ChartSpec(kind=kind, x=x, y=y, title=title)


def _summarize(call: ToolCall, outcome: ToolOutcome) -> str:
    if not outcome.ok:
        return str(outcome.content)[:300]
    content = outcome.content if isinstance(outcome.content, dict) else {}
    if call.name == QUERY_TOOL:
        return f"{content.get('row_count', 0)} linha(s) retornada(s)"
    if call.name == "list_tables":
        return f"{len(content.get('tables', []))} tabela(s) encontrada(s)"
    if call.name == "describe_table":
        return f"{len(content.get('columns', []))} coluna(s) em {content.get('name', '?')}"
    return "ok"


def _for_model(tool: str, outcome: ToolOutcome) -> str:
    if not outcome.ok:
        return f"ERRO: {outcome.content}"
    content = outcome.content
    if tool == QUERY_TOOL and isinstance(content, dict):
        rows = content.get("rows", [])
        content = {
            **content,
            "rows": rows[:MODEL_PREVIEW_ROWS],
            "rows_omitted_from_preview": max(len(rows) - MODEL_PREVIEW_ROWS, 0),
        }
    return json.dumps(content, ensure_ascii=False, default=str)
