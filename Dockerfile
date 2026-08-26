FROM python:3.14-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /uvx /usr/local/bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
COPY README.md LICENSE ./
RUN uv sync --locked --no-dev --no-editable

FROM python:3.14-slim-bookworm
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=builder --chown=10001:10001 /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 SKELETAL_LOG_TO_FILE=false
USER 10001
ENTRYPOINT ["skeletal"]
CMD ["--help"]
