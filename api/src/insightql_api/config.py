from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_ignore_empty=True)

    mcp_server_url: str = "http://mcp-server:8001/mcp"
    llm_base_url: str = "http://ollama:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen2.5:7b"
    llm_temperature: float | None = None
    llm_reasoning_effort: str | None = None
    llm_timeout_seconds: float = 120.0
    agent_max_steps: int = 8
