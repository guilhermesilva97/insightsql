# 03 - Execução

Este documento conta como o projeto foi construído, na ordem em que as coisas aconteceram. Ele registra o que foi feito, por que foi feito daquele jeito e o que deu errado no caminho.

## Visão geral das etapas

| # | Etapa | Entregável |
|---|---|---|
| 1 | Modelagem e seed do banco | Schema e dados determinísticos para PostgreSQL e MySQL |
| 2 | Guardrail de SQL | `SqlGuard` com testes cobrindo ataques conhecidos |
| 3 | Servidor MCP | Três ferramentas sobre um núcleo em Clean Architecture |
| 4 | Agente | Loop de tool calling, autocorreção e saída estruturada |
| 5 | Streaming | Endpoint SSE com o raciocínio do agente |
| 6 | Front-end | Tela de pergunta, trilha de ferramentas e visualização |
| 7 | Containers | Dockerfiles multi-stage e compose com profiles |
| 8 | Pipeline | CI com testes, integração, smoke test, evals e publicação |
| 9 | Evals | Conjunto de perguntas de referência e métrica de acurácia |
| 10 | Teste com LLM real | Ajustes de configuração, schema e evals guiados pelos resultados |

---

## Etapa 1: banco e dados

**Objetivo:** ter um domínio que todo mundo entende (e-commerce) com dados suficientes para perguntas interessantes.

- Cinco tabelas: `categories`, `products`, `customers`, `orders`, `order_items`.
- O seed é **determinístico**: os dados são gerados com aritmética modular (`generate_series` no PostgreSQL, CTE recursiva no MySQL), sem `random()`. Isso é essencial para os evals, porque a resposta certa precisa ser a mesma em qualquer máquina.
- **Descrições de negócio ficam no próprio catálogo do banco** (`COMMENT ON` no PostgreSQL, `COMMENT` no MySQL). Por exemplo, a coluna `orders.status` explica que pedidos `cancelled` não contam como receita. O servidor MCP lê essas descrições pelo SQLAlchemy e as entrega ao agente. Assim a regra de negócio mora junto do dado, não num prompt.
- Criei o usuário `insightql_reader` só com `SELECT`, `statement_timeout` de 5s e `default_transaction_read_only`. A aplicação **nunca** conecta com o usuário dono do banco.

## Etapa 2: guardrail de SQL

**Decisão:** validar o SQL com um parser de verdade (sqlglot) em vez de regex. Uma regex como `^SELECT` deixa passar `SELECT 1; DROP TABLE orders` e bloqueia `WITH ... SELECT`.

O que o `SqlGuard` faz, em ordem:

1. Faz o parse no dialeto do banco e exige exatamente uma instrução.
2. Exige que a raiz seja uma *query* (`SELECT`, `WITH`, `UNION`) e procura qualquer nó de escrita na árvore, inclusive `SELECT ... INTO`.
3. Bloqueia tabelas de sistema.
4. Bloqueia funções perigosas.
5. Impõe `LIMIT`. Em `UNION` não dá para aplicar o limite direto, então a consulta é embrulhada num `SELECT * FROM (...) LIMIT n`.

Escrevi os testes **antes** de considerar o guard pronto, com uma lista de ataques comuns.

> **Problema encontrado:** o teste de `SELECT version()` falhou. O sqlglot não trata `version()` como função anônima: ele converte para um nó tipado `CurrentVersion`, cujo nome SQL é `CURRENT_VERSION`. A blocklist comparava com `version` e deixava passar.
>
> **Correção:** incluí os nomes canônicos (`current_version`, `current_user`) na blocklist.
>
> **Lição:** quando se usa um parser, a validação precisa ser feita sobre a forma normalizada da árvore, não sobre o texto que o usuário digitou.

## Etapa 3: servidor MCP

**Decisão:** expor o acesso a dados como um servidor MCP separado, e não como funções dentro do agente ([ADR 0001](adr/0001-mcp-como-fronteira-de-dados.md)).

- Três ferramentas pequenas, com descrições pensadas para o modelo: `list_tables`, `describe_table` e `run_query`.
- As descrições vão como parâmetro do decorator `@server.tool(description=...)`. Docstrings também funcionariam, mas assim a descrição fica explícita como parte do contrato.
- O servidor publica **instruções** no handshake MCP com o dialeto e o limite de linhas. Qualquer cliente MCP recebe esse contexto automaticamente.
- O acesso ao banco é síncrono (SQLAlchemy), mas o FastMCP é assíncrono. Cada ferramenta delega para `anyio.to_thread.run_sync`, para não travar o event loop.

> **Problema encontrado:** colunas `NUMERIC` do PostgreSQL chegam como `Decimal`, que não é serializável em JSON.
>
> **Correção:** o adaptador normaliza o resultado com pandas (`Decimal` vira `float`, datas viram ISO 8601) antes de devolver.

## Etapa 4: o agente

O caso de uso `AskQuestion` implementa o loop clássico de *tool calling*:

1. Abre uma sessão MCP e lista as ferramentas.
2. Acrescenta uma ferramenta local, `present_answer`, que obriga o modelo a encerrar com saída estruturada: resumo, tipo de gráfico, eixo X e séries Y.
3. Repete até `max_steps`: chama o modelo, executa as ferramentas pedidas e devolve os resultados.

Decisões importantes:

- **Erros são devolvidos ao modelo** como `ERRO: <mensagem do banco>`. Na prática, é isso que faz o agente acertar consultas difíceis: ele erra o nome de uma coluna, lê o erro, chama `describe_table` e corrige.
- **O modelo vê só uma prévia** de 30 linhas de cada resultado. A tabela completa vai direto para o front, sem passar de novo pelo LLM. Isso economiza tokens e evita alucinação sobre os dados.
- **O gráfico é validado contra o resultado real.** Se o modelo pedir `y=["receita"]` e a coluna se chamar `total`, a API devolve tabela em vez de um gráfico vazio.
- **Limite de passos** para o agente nunca entrar em loop infinito.

> **Problema encontrado:** o adaptador enviava `temperature=0` fixo. Funcionava com Ollama e com modelos como `gpt-4o-mini`, mas modelos de raciocínio (família `gpt-5`, `o3`, `o4`) rejeitam qualquer `temperature` diferente do padrão e, em troca, aceitam `reasoning_effort`.
>
> **Correção:** os dois parâmetros passaram a ser opcionais (`LLM_TEMPERATURE` e `LLM_REASONING_EFFORT`) e só são enviados quando configurados. Um teste garante que, sem configuração, nenhum deles vai na requisição.
>
> **Lição:** "compatível com OpenAI" não significa que todos os modelos aceitam os mesmos parâmetros. O adaptador deve enviar o mínimo e deixar o resto configurável.

O domínio do agente (`Message`, `ToolCall`, `ModelTurn`) não depende do SDK da OpenAI. O adaptador `OpenAICompatibleModel` faz a tradução. Com isso, os testes do agente rodam com um modelo roteirizado, sem rede.

## Etapa 5: streaming com SSE

O front precisa mostrar cada ferramenta assim que ela é chamada ([ADR 0004](adr/0004-sse-para-streaming.md)).

> **Problema encontrado:** a primeira versão iterava o caso de uso direto dentro do gerador do `StreamingResponse`. O cliente MCP usa *task groups* do anyio, que precisam ser abertos e fechados na mesma task. Quando o navegador fecha a conexão no meio, o Starlette encerra o gerador a partir de outro contexto, e o anyio acusa erro de *cancel scope*.
>
> **Correção:** o agente roda numa task própria (`_produce`), que publica eventos numa `asyncio.Queue`. O gerador HTTP só consome a fila e, ao terminar, cancela a task produtora. Assim o ciclo de vida da sessão MCP fica isolado do ciclo de vida da conexão HTTP.

Falhas de infraestrutura (LLM fora do ar, MCP indisponível) viram um evento `error` com mensagem amigável. O stack trace vai só para o log.

## Etapa 6: front-end

- React + TypeScript + Vite, com Recharts para os gráficos.
- `EventSource` só aceita `GET`, e a pergunta vai no corpo de um `POST`. Por isso escrevi um parser de SSE próprio sobre `fetch` + `ReadableStream`, testado para eventos quebrados entre pacotes de rede e para finais de linha `\r\n`.
- O hook `useAgent` concentra o estado: trilha de passos, resposta e erro. Se o stream terminar sem resposta nem erro, a tela mostra que a conexão caiu, em vez de ficar carregando para sempre.
- Os componentes não sabem nada de SSE: recebem dados prontos.
- Tema claro e escuro por variáveis CSS e layout responsivo.

## Etapa 7: containers

- **Dockerfiles multi-stage**, com o mesmo arquivo gerando a imagem de teste e a de produção:
  - `test`: instala dependências de desenvolvimento e roda lint e testes;
  - `runtime`: imagem enxuta, com usuário sem privilégios;
  - `evals`: só na API.
- O `package-lock.json` também foi gerado dentro de um container Node, para não depender da versão de Node da máquina.
- O **compose usa profiles** para não subir o que não é necessário:
  - padrão: postgres, mcp-server, api, web;
  - `local-llm`: Ollama;
  - `mysql`: banco alternativo;
  - `test`: testes de cada serviço;
  - `evals`: avaliação com LLM real.
- O nginx serve o build estático e faz proxy de `/api`, com `proxy_buffering off`. Sem isso, o nginx acumula a resposta e os eventos SSE chegam todos de uma vez no final.

## Etapa 8: pipeline

Detalhada em [04-pipeline.md](04-pipeline.md). O princípio foi: **o CI roda exatamente os mesmos comandos que eu rodo localmente**. Não existe um "jeito de rodar no CI" diferente do jeito de rodar na máquina.

## Etapa 9: evals

Testes unitários garantem que o código funciona. Evals medem se o **agente responde certo**, o que depende do modelo, do prompt e das descrições do schema.

- `api/evals/golden.json` tem perguntas com o SQL de referência.
- Para cada pergunta, o script executa o SQL de referência pelo mesmo servidor MCP, roda o agente e compara os resultados.
- **A comparação usa só os valores numéricos de cada linha, sem considerar a ordem.** O agente pode chamar a coluna de `total` ou `receita`, formatar o mês como `2025-01` ou `2025-01-01T00:00:00` e ordenar de outro jeito: nada disso deveria reprovar uma resposta correta.
- O processo falha se a acurácia ficar abaixo de `EVALS_MIN_ACCURACY` (75%).

Limitação conhecida: as colunas são comparadas de forma independente, então uma resposta com os números certos nas linhas erradas passaria. Para este conjunto de perguntas, o risco é baixo.

## Etapa 10: primeiro teste com um LLM real

Até aqui, todos os testes usavam um modelo roteirizado. O primeiro teste com a OpenAI (`gpt-5.6-luna`) trouxe quatro descobertas.

> **Problema 1: o modelo recusou a chamada.** A API devolveu `400: Function tools with reasoning_effort are not supported ... in /v1/chat/completions`. Esse modelo não aceita ferramentas e raciocínio ao mesmo tempo no endpoint de chat.
>
> **Correção:** `LLM_REASONING_EFFORT=none`, que é configuração e não exige mudança de código, graças aos parâmetros opcionais da etapa 4. A alternativa seria migrar para a Responses API, mas ela não é suportada pelo Ollama e quebraria a portabilidade ([ADR 0003](adr/0003-provedor-llm-compativel-openai.md)).

> **Problema 2: um caso do eval tinha gabarito ambíguo.** "Quais os 5 produtos mais vendidos em unidades?" falhava sempre. Investigando, 12 dos 15 produtos tinham exatamente 546 unidades vendidas: o seed com aritmética modular distribui as vendas de forma uniforme. Com empate, qualquer combinação de 5 produtos está certa, e o eval reprovava respostas corretas.
>
> **Correção:** troquei o caso por "5 produtos com maior receita", que não tem empate. Melhorar a distribuição do seed ficou como próximo passo.

> **Problema 3: o agente aplicava a regra de negócio fora de contexto.** A descrição da coluna `orders.status` dizia que pedidos cancelados "não contam como receita". O modelo generalizava e excluía cancelados até ao *contar* pedidos, e até quando a pergunta dizia "considerando todos os pedidos".
>
> **Tentativa 1:** adicionar ao prompt uma regra dizendo que o pedido explícito do usuário prevalece. **Não resolveu**: o modelo deu mais peso à descrição da coluna do que ao prompt.
>
> **Correção:** reescrevi a descrição da coluna no banco, deixando o escopo explícito: exclui cancelados em métricas de receita, contagens incluem todos os status e o pedido explícito do usuário prevalece. Os casos passaram.
>
> **Lição:** a descrição do schema *é* parte do prompt, e muitas vezes a parte que o modelo mais respeita. Regra de negócio ambígua no catálogo vira resposta errada.

> **Problema 4: o eval reprovava respostas certas com colunas extras.** O agente às vezes devolve `product_id` ou `units_sold` junto da receita. A comparação antiga usava todos os valores numéricos da linha, então qualquer coluna a mais reprovava.
>
> **Correção:** a comparação passou a ser por coluna. O número de linhas precisa bater e cada coluna numérica do gabarito precisa existir na resposta; colunas extras são ignoradas. Ganhou 5 testes unitários.

**Resultado:** a acurácia subiu de 88% para 100% nas rodadas finais. Como o modelo não é determinístico, a nota variou entre 88% e 100% ao longo das execuções. É por isso que o limite mínimo da pipeline é 75%, e não 100%.

---

## Validações realizadas

| Verificação | Resultado |
|---|---|
| Testes do mcp-server (unitários + integração com PostgreSQL) | 33 aprovados |
| Testes da API (agente, endpoint SSE, adaptador do LLM e comparação dos evals) | 15 aprovados |
| Testes e typecheck do front | 4 aprovados |
| Ferramentas MCP chamadas pela API via HTTP entre containers | OK |
| `DELETE` via MCP bloqueado pelo guard | OK |
| `DELETE` direto no banco com o usuário da aplicação | Recusado pelo PostgreSQL |
| Workflow do GitHub Actions validado com actionlint | Sem erros |
| Perguntas reais com OpenAI (`gpt-5.6-luna`) pela stack completa | Respostas corretas em 5 a 7 segundos |
| Pedido de escrita ("apague os pedidos cancelados") com LLM real | Recusado pelo agente |
| Evals com LLM real | 100% na rodada final (variou entre 88% e 100%) |

## Próximos passos

- Perguntas de acompanhamento ("e no ano anterior?") com memória de conversa.
- Camada semântica com métricas nomeadas (receita, ticket médio) para reduzir ambiguidade.
- Cache de respostas por pergunta normalizada.
- Traces de LLM com OpenTelemetry (tokens, custo e latência por passo).
- Ampliar o conjunto de evals e rodar contra MySQL também.
- Seed com distribuição de vendas menos uniforme, para perguntas de ranking ficarem interessantes.
- Rodar cada caso do eval mais de uma vez e reportar a taxa de acerto, para medir a variação do modelo.
