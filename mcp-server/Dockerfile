FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src

FROM base AS test
RUN pip install ".[dev]"
COPY tests ./tests
CMD ["sh", "-c", "ruff check src tests && ruff format --check src tests && pytest -v"]

FROM base AS runtime
RUN pip install . && useradd --create-home --uid 10001 app
USER app
EXPOSE 8001
CMD ["python", "-m", "insightql_mcp"]
