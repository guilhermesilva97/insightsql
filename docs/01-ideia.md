# 01 - Ideia

## O problema

Em praticamente toda empresa que trabalhei, a mesma cena se repete: alguém da área de negócio precisa de um número ("quanto vendemos por região no último trimestre?") e abre um chamado para o time de dados ou de desenvolvimento. A resposta demora horas ou dias, não porque a consulta seja difícil, mas porque existe uma fila de pessoas que sabem SQL.

Já implementei uma solução desse tipo em ambiente corporativo: um assistente baseado em LLM que converte linguagem natural em queries e gera gráficos automaticamente. O InsightQL é a reconstrução dessa ideia do zero, com dados fictícios, aplicando o que aprendi e o que eu faria diferente.

## O que eu queria provar

1. Que dá para colocar um LLM perto de um banco de produção **com segurança**, sem confiar cegamente no SQL gerado.
2. Que o acesso a dados pode ser um **componente reutilizável** (servidor MCP), e não um detalhe escondido dentro do agente.
3. Que a qualidade de um agente pode ser **medida** e acompanhada na pipeline, como qualquer outro teste.
4. Que o usuário confia mais quando **vê o raciocínio**: quais tabelas o agente leu, qual SQL rodou, quantas linhas voltaram.

## Usuários

| Persona | Necessidade |
|---|---|
| Analista de negócio | Fazer perguntas sem saber SQL e receber gráfico pronto |
| Gestor | Respostas rápidas em reuniões, com números confiáveis |
| Desenvolvedor / analista de dados | Auditar o SQL gerado e reaproveitar o servidor MCP no próprio editor |

## Escopo

**Dentro do escopo**

- Perguntas em português sobre um banco de e-commerce (clientes, produtos, pedidos, itens).
- Descoberta de schema pelo próprio agente, sem schema fixo no prompt.
- Execução somente leitura com limite de linhas e timeout.
- Escolha automática de visualização (barra, linha, pizza ou tabela).
- Suporte a PostgreSQL e MySQL.
- Funcionamento com LLM pago (OpenAI) ou local (Ollama).
- Evals automatizados.

**Fora do escopo (por enquanto)**

- Autenticação e multi-tenant.
- Histórico de conversas e perguntas de acompanhamento.
- Escrita no banco, mesmo que assistida.
- Cache de respostas.

## Requisitos não funcionais

| Requisito | Como é atendido |
|---|---|
| Segurança | Guardrail de SQL + usuário read-only + transação read-only + timeout |
| Observabilidade da IA | Cada tool call é transmitida para a tela e registrada no log |
| Portabilidade | Tudo em containers; provedor de LLM configurável por variável de ambiente |
| Testabilidade | Portas e adaptadores permitem testar o agente com modelo e ferramentas falsas |
| Reprodutibilidade | Seed determinístico: os mesmos dados em toda máquina, o que torna os evals estáveis |

## Critérios de sucesso

- Acurácia mínima de 75% no conjunto de evals.
- Nenhuma instrução de escrita chega ao banco, comprovado por testes de integração.
- Subir o projeto do zero com dois comandos.
