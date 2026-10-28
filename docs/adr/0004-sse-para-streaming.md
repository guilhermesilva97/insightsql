# ADR 0004: SSE para transmitir o raciocínio do agente

**Status:** aceita

## Contexto

Uma pergunta pode levar de 5 a 30 segundos, com várias chamadas de ferramenta. Uma tela parada nesse tempo passa a sensação de erro e esconde justamente o que gera confiança: ver o agente consultando o banco.

## Decisão

`POST /api/questions` responde com `text/event-stream`. Os eventos são `tool_started`, `tool_finished`, `answer` e `error`. O front consome com `fetch` + `ReadableStream` e um parser próprio, porque `EventSource` não aceita `POST`.

## Consequências

- O usuário acompanha cada passo em tempo real.
- O fluxo é unidirecional e funciona em HTTP comum, atravessando proxies sem configuração especial além de `proxy_buffering off`.
- Como não há reconexão automática, se a conexão cair o front mostra o erro e o usuário pergunta de novo.

## Alternativas consideradas

- **WebSocket:** bidirecional, mas mais complexo de operar e desnecessário aqui.
- **Polling:** simples, mas com latência e carga extras.
