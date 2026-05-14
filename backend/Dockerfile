# Build stage
FROM python:3.10-slim AS builder

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-editable --compile-bytecode

# Runtime stage
FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY --from=builder /build/.venv /app/.venv
RUN find /app/.venv/bin -type f -executable \
    | xargs grep -l "^#!/build/.venv" 2>/dev/null \
    | xargs sed -i 's|#!/build/.venv/bin/python|#!/app/.venv/bin/python|g' || true
COPY --chown=appuser:appuser . .

RUN mkdir -p data models && chown -R appuser:appuser /app

USER appuser

RUN mkdir -p /home/appuser/.insightface/models

ENV PATH="/app/.venv/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]