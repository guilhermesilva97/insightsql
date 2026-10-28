# ADR 0001: MCP como fronteira entre o agente e os dados

**Status:** aceita

## Contexto

O agente precisa listar tabelas, ler schemas e executar consultas. O caminho mais curto seria registrar essas funções direto no código do agente, como *function calling* da OpenAI.

## Decisão

O acesso a dados fica num **servidor MCP** separado (FastMCP, transporte *streamable HTTP*). A API do agente é apenas um cliente MCP: descobre as ferramentas em tempo de execução e as converte para o formato de *function calling* do modelo.

## Consequências

**Positivas**

- O servidor de dados é reutilizável: o mesmo servidor funciona no Claude Desktop, no Cursor ou em outro agente, sem nenhuma alteração.
- Segurança concentrada: guardrails, credenciais e timeout ficam num único processo, que é o único com acesso ao banco.
- O agente não depende do banco. Adicionar ferramentas novas (por exemplo, `explain_query`) não exige mudar a API.
- Os dois lados escalam e são implantados de forma independente.

**Negativas**

- Um salto de rede a mais por chamada de ferramenta, desprezível perto da latência do LLM.
- Mais um container para operar.
- É preciso tratar o ciclo de vida da sessão MCP com cuidado em respostas em streaming (ver [03-execucao.md](../03-execucao.md), etapa 5).

## Alternativas consideradas

- **Funções locais no agente:** mais simples, mas acopla o agente ao banco e não é reutilizável.
- **API REST própria para dados:** funcionaria, mas eu teria que reinventar descoberta de ferramentas, schemas de entrada e instruções, que o MCP já padroniza.
