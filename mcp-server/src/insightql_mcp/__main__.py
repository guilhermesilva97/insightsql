from insightql_mcp.config import Settings
from insightql_mcp.presentation.server import build_server


def main() -> None:
    build_server(Settings()).run(transport="streamable-http")


if __name__ == "__main__":
    main()
