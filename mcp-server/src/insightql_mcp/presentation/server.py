from dataclasses import asdict
from typing import Any

import anyio
from mcp.server.fastmcp import FastMCP

from insightql_mcp.application.service import InsightService
from insightql_mcp.config import Settings
from insightql_mcp.domain.sql_guard import QueryPolicy
from insightql_mcp.infrastructure.database import SqlAlchemyDatabase

_INSTRUCTIONS = (
    "Servidor de dados analíticos de um e-commerce (banco {dialect}). "
    "Fluxo recomendado: list_tables para descobrir as tabelas, "
    "describe_table para ler colunas, chaves e descrições, "
    "e run_query para executar uma única consulta SELECT no dialeto {dialect}. "
    "O resultado é limitado a {max_rows} linhas."
)


def build_service(settings: Settings) -> InsightService:
    database = SqlAlchemyDatabase(settings.database_url, settings.query_timeout_ms)
    return InsightService(
        catalog=database,
        executor=database,
        policy=QueryPolicy(max_rows=settings.max_rows),
    )


def build_server(settings: Settings, service: InsightService | None = None) -> FastMCP:
    service = service or build_service(settings)
    server = FastMCP(
        "insightql",
        instructions=_INSTRUCTIONS.format(dialect=service.dialect, max_rows=settings.max_rows),
        host=settings.mcp_host,
        port=settings.mcp_port,
    )
    register_tools(server, service)
    return server


def register_tools(server: FastMCP, service: InsightService) -> None:
    @server.tool(
        name="list_tables",
        description="Lista as tabelas disponíveis para consulta, com uma descrição de cada uma.",
    )
    async def list_tables() -> dict[str, Any]:
        tables = await anyio.to_thread.run_sync(service.list_tables)
        return {"dialect": service.dialect, "tables": [asdict(t) for t in tables]}

    @server.tool(
        name="describe_table",
        description=(
            "Retorna colunas, tipos, chave primária, chaves estrangeiras e descrições de negócio "
            "de uma tabela. Use antes de escrever SQL."
        ),
    )
    async def describe_table(table: str) -> dict[str, Any]:
        schema = await anyio.to_thread.run_sync(service.describe_table, table)
        return asdict(schema)

    @server.tool(
        name="run_query",
        description=(
            "Executa uma única consulta SELECT somente leitura e retorna colunas e linhas. "
            "Consultas de escrita, múltiplas instruções e tabelas de sistema são rejeitadas."
        ),
    )
    async def run_query(sql: str) -> dict[str, Any]:
        executed = await anyio.to_thread.run_sync(service.run_query, sql)
        return {
            "sql": executed.sql,
            "columns": list(executed.result.columns),
            "rows": list(executed.result.rows),
            "row_count": len(executed.result.rows),
            "truncated": executed.result.truncated,
        }
