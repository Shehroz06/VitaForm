FROM python:3.13-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl fonts-liberation \
    fonts-crosextra-carlito fonts-crosextra-caladea \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libcairo2 shared-mime-info \
    texlive-latex-base texlive-latex-recommended texlive-latex-extra \
    texlive-fonts-recommended lmodern \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

EXPOSE 8000

# --- Development: docker-compose.yml bind-mounts source over this, so the
# COPY below only matters when this stage is built/run standalone. Runs as
# root with --reload to match that bind-mount, edit-and-see workflow. ---
FROM base AS dev
COPY . .
RUN uv sync --frozen
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Production: code is baked into the image (no bind mount), runs as an
# unprivileged user, no --reload, and a HEALTHCHECK that exercises the app
# (app/api/v1/health.py's real DB round-trip) instead of just confirming
# the process is up. This is the default target for a plain `docker build`
# with no --target, so an unqualified build never produces a root/dev image. ---
FROM base AS production
COPY . .
RUN uv sync --frozen

RUN groupadd --system app && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app
USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
