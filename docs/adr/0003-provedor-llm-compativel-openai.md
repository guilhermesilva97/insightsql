# ADR 0003: adaptador único para APIs compatíveis com OpenAI

**Status:** aceita

## Contexto

Quero que qualquer pessoa consiga rodar o projeto sem cartão de crédito, mas também quero demonstrar o uso de um modelo comercial. Manter um SDK por fornecedor multiplica o código e os testes.

## Decisão

- O domínio define as próprias estruturas (`Message`, `ToolCall`, `ModelTurn`), e a aplicação depende só da porta `LanguageModel`.
- Existe um único adaptador, `OpenAICompatibleModel`, configurado por `LLM_BASE_URL`, `LLM_API_KEY` e `LLM_MODEL`.
- O padrão é o Ollama local (`qwen2.5:7b`, que suporta *tool calling*). Com três variáveis de ambiente, o projeto passa a usar OpenAI, Azure OpenAI, vLLM ou outro serviço compatível.

## Consequências

- A troca de provedor é configuração, não código.
- Os testes do agente usam um `ScriptedModel` e não dependem de rede.
- Recursos exclusivos de um fornecedor (por exemplo, *prompt caching* específico) exigiriam um adaptador dedicado. A porta já permite isso sem mexer no caso de uso.
- Modelos locais pequenos erram mais em consultas com vários `JOIN`. Os evals deixam essa diferença visível.
