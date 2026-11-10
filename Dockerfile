# webapp build
FROM node:22-alpine AS ui
WORKDIR /ui
COPY webapp/package.json webapp/package-lock.json ./
RUN npm ci
COPY webapp/ ./
RUN npm run build

# backend build
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.2 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# build in the runtime path: venv console scripts (uvicorn, alembic) hardcode it in their shebangs
WORKDIR /app

COPY api/pyproject.toml api/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY api/alembic.ini ./
COPY api/migrations ./migrations
COPY api/app ./app
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime

# Fixed UID so host-side chown of bind mounts (e.g. /app/.state) is predictable.
RUN groupadd -r -g 10001 todo && useradd -r -g todo -u 10001 -m -d /home/todo todo

WORKDIR /app
COPY --from=builder --chown=todo:todo /app /app
COPY --from=ui --chown=todo:todo /ui/dist /app/webapp
# SQLite lives here (DATABASE_PATH default is relative to /app); bind-mount it to persist
RUN install -d -o todo -g todo /app/.state
VOLUME /app/.state
USER todo

EXPOSE 8080

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WEBAPP_DIR=/app/webapp

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info", "--timeout-graceful-shutdown", "5"]
