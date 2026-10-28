from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001
    max_rows: int = 500
    query_timeout_ms: int = 5000
