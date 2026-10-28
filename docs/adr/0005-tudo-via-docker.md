# ADR 0005: Docker como única dependência de desenvolvimento e CI

**Status:** aceita

## Contexto

O projeto mistura Python, Node, PostgreSQL, MySQL e, opcionalmente, um LLM local. Exigir que cada pessoa instale as versões certas de tudo é a principal razão de projetos de portfólio não rodarem na máquina de quem avalia.

## Decisão

- Cada serviço tem um Dockerfile multi-stage com *targets* `test` e `runtime` (e `evals` na API).
- O `docker-compose.yml` usa *profiles* para separar o que roda sempre do que é opcional: `local-llm`, `mysql`, `test` e `evals`.
- A pipeline executa os mesmos comandos `docker compose` usados localmente.

## Consequências

- Rodar, testar e avaliar exige apenas Docker.
- O ambiente do CI é idêntico ao local, o que elimina o "na minha máquina funciona".
- Builds são mais lentos que rodar `pytest` direto. O cache de camadas e o cache do GitHub Actions compensam boa parte disso.
- Para depurar com breakpoint no editor, ainda é possível rodar um serviço fora do container, apontando para os demais no compose.
