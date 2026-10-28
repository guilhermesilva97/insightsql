# InsightQL

![CI](https://github.com/guilhermesilva97/insightsql/actions/workflows/ci.yml/badge.svg)

Agente de IA que responde perguntas de negócio em linguagem natural consultando um banco relacional. O agente descobre o schema, escreve o SQL, se corrige quando erra e devolve a resposta com gráfico, tabela e o SQL executado para auditoria.

O acesso aos dados é feito por um **servidor MCP (Model Context Protocol)** independente, que também pode ser plugado no Claude Desktop, no Cursor ou em qualquer cliente MCP.

```
Pergunta: "Qual a receita por categoria, sem pedidos cancelados?"

  list_tables      → 5 tabelas encontradas
  describe_table   → 5 colunas em order_items
  describe_table   → 4 colunas em orders
  run_query        → 5 linhas retornadas

Resposta: "Eletrônicos lidera com R$ 4,23 mi, seguido de Esporte com R$ 1,50 mi..."  + gráfico de barras
```

## Arquitetura em uma imagem

```mermaid
flowchart LR
    U[Usuário] --> W[Web<br/>React + nginx]
    W -- SSE --> A[API do agente<br/>FastAPI]
    A -- chat + tools --> L[(LLM<br/>OpenAI / Ollama)]
    A -- MCP streamable HTTP --> M[MCP Server<br/>FastMCP]
    M -- usuário read-only --> D[(PostgreSQL<br/>ou MySQL)]
    C[Claude Desktop / Cursor] -. MCP .-> M
```

Detalhes em [docs/02-arquitetura.md](docs/02-arquitetura.md).

## Destaques técnicos

- **MCP como fronteira**: o agente não conhece o banco; ele só enxerga ferramentas expostas pelo servidor MCP.
- **Defesa em profundidade no SQL**: parser (sqlglot) bloqueia escrita, múltiplas instruções, catálogos e funções perigosas; o banco usa um usuário somente leitura com timeout.
- **Autocorreção**: erros do banco voltam para o modelo, que ajusta o SQL e tenta de novo.
- **Streaming do raciocínio**: cada chamada de ferramenta aparece em tempo real na tela via Server-Sent Events.
- **Agnóstico de provedor**: qualquer API compatível com OpenAI (OpenAI, Ollama local, Azure OpenAI, vLLM).
- **Evals**: perguntas de referência com SQL esperado medem a acurácia do agente na pipeline.
- **Clean Architecture** em todos os serviços Python: `domain`, `application`, `infrastructure`, `presentation`.
- **Tudo via Docker**: rodar, testar, lintar e avaliar não exige nada instalado além do Docker.

## Como rodar

Pré-requisito: Docker com Compose v2.

```bash
cp .env.example .env
```

### Opção 1: LLM local com Ollama (sem custo)

```bash
docker compose --profile local-llm up -d --build
docker compose --profile local-llm run --rm ollama-pull
```

O primeiro comando sobe tudo; o segundo baixa o modelo definido em `LLM_MODEL` (padrão `qwen2.5:7b`, cerca de 4,7 GB).

### Opção 2: OpenAI

No `.env`:

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0
LLM_REASONING_EFFORT=
```

Modelos de raciocínio (família `gpt-5`, `o3`, `o4`) não aceitam `temperature`: deixe `LLM_TEMPERATURE` vazio. Alguns deles também recusam ferramentas junto com raciocínio no endpoint de chat; nesse caso use `LLM_REASONING_EFFORT=none` (testado com `gpt-5.6-luna`).

```bash
docker compose up -d --build
```

Acesse **http://localhost:8080**.

### Usando MySQL no lugar do PostgreSQL

No `.env`:

```env
DATABASE_URL=mysql+pymysql://insightql_reader:reader@mysql:3306/insightql
```

```bash
docker compose --profile mysql up -d --build
```

## Testes, lint e evals

```bash
docker compose --profile test run --rm --build mcp-test
docker compose --profile test run --rm --build api-test
docker compose --profile test run --rm --build web-test
docker compose --profile evals run --rm --build evals
```

`mcp-test` sobe um PostgreSQL real e roda também os testes de integração, incluindo a prova de que o usuário do banco não consegue escrever mesmo que o guardrail falhe.

## Conectando o servidor MCP em outros clientes

Com a stack de pé, o servidor fica em `http://localhost:8001/mcp`.

- **MCP Inspector**: `npx @modelcontextprotocol/inspector`, transporte *Streamable HTTP*, URL acima.
- **Claude Desktop**: adicione em `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "insightql": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:8001/mcp"]
    }
  }
}
```

## Estrutura

```
insightql/
├── database/            scripts de schema, seed e usuário read-only (PostgreSQL e MySQL)
├── mcp-server/          servidor MCP: guardrails de SQL, catálogo e execução
├── api/                 agente: loop de tool calling, cliente MCP, SSE e evals
├── web/                 React + Vite servido por nginx
├── docs/                ideia, arquitetura, execução, pipeline e ADRs
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Documentação

| Documento | Conteúdo |
|---|---|
| [01 - Ideia](docs/01-ideia.md) | Problema, objetivos, escopo e requisitos |
| [02 - Arquitetura](docs/02-arquitetura.md) | Diagramas C4, fluxo do agente e camadas |
| [03 - Execução](docs/03-execucao.md) | Como o projeto foi construído, etapa por etapa, e os problemas encontrados |
| [04 - Pipeline](docs/04-pipeline.md) | Guia da pipeline de CI/CD e como configurá-la |
| [ADRs](docs/adr) | Registro das decisões de arquitetura |
