FROM python:3.14-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY main.py ./

EXPOSE 8000

ENV MCP_PORT=8000

ENTRYPOINT ["uv", "run", "python", "main.py"]
CMD ["--transport", "stdio"]
