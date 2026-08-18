# AI Career Platform

A career operating system: one structured profile, from which the AI generates real, exportable
career documents (a job-targeted CV/resume, a cover letter, LinkedIn "About" text) on demand. The
database is always the source of truth — the AI only selects and arranges real profile data and
writes connective prose; it never invents experience, projects, or achievements that aren't there.
The profile can also be bootstrapped by uploading an existing CV as a PDF — the app extracts and
classifies the content, but nothing is written until you review and confirm it.

Backend: FastAPI + SQLAlchemy (async) + Alembic + PostgreSQL.
Frontend: Next.js (App Router) + TypeScript + Tailwind + shadcn/ui.
AI: provider-agnostic (Gemini, Groq, OpenRouter, OpenAI, Anthropic — swap via config, not code).

---

## Prerequisites

- Docker + Docker Compose (the only hard requirement for local development)
- For running backend tooling outside a container: Python 3.13 and [`uv`](https://docs.astral.sh/uv/)
- For running frontend tooling outside a container: Node 22+

## Quick start

```bash
# 1. Backend environment
cp backend/.env.example backend/.env
# then fill in at least one AI provider key (see "AI providers" below) — everything
# else has a working default.

# 2. Frontend environment
cp frontend/.env.example frontend/.env

# 3. Boot the full stack (Postgres + Redis + backend + frontend)
docker compose -f docker/docker-compose.yml up -d --build

# 4. Apply database migrations
cd backend && uv run alembic upgrade head
```

- Backend: http://localhost:8000 (`GET /api/v1/health` should return `{"success": true, ...}`)
- API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

Tear down with `docker compose -f docker/docker-compose.yml down` (add `-v` to also drop the
Postgres volume — only do this if you actually want a clean database).

## Environment variables

All settings live in `backend/.env` (see `backend/.env.example` for the full list with defaults)
and `frontend/.env` (`NEXT_PUBLIC_API_URL`, pointing at the backend).

**Required to do anything useful:**
- `DATABASE_URL`, `REDIS_URL` — already correct for the Docker Compose setup, no changes needed.
- `JWT_SECRET` — change this to a real secret before anything beyond local development.

**AI providers** (`backend/.env`) — at least one is needed for resume/cover-letter/LinkedIn
generation to work; everything else in the app (profile CRUD, manual resume export, job/ATS
analysis) works without any AI key configured:
- `AI_DEFAULT_PROVIDER` picks the primary provider; `AI_FALLBACK_PROVIDERS` is an ordered list
  tried if the default fails or isn't configured (e.g. `["groq","openrouter"]`).
- Supported: `gemini`, `groq`, `openrouter`, `openai`, `anthropic`. Set the matching
  `<PROVIDER>_API_KEY` for whichever you use. Gemini's free tier
  (https://aistudio.google.com/apikey) and Groq's free tier (https://console.groq.com/keys) are
  both good, zero-cost defaults to start with.
- Switching providers is a config change only — no code changes required.

**Email (OTP / verification / password reset):**
- `EMAIL_PROVIDER=console` (default) — verification/reset emails are logged to the backend
  container's stdout instead of being sent. Fine for local development: run
  `docker compose -f docker/docker-compose.yml logs -f backend` and copy the token/link from the
  log line after triggering registration or "forgot password".
- `EMAIL_PROVIDER=smtp` — sends real email via SMTP. Set `SMTP_HOST`, `SMTP_PORT`,
  `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_ADDRESS`, `SMTP_FROM_NAME`. Works with any SMTP
  endpoint — a relay, or the SMTP interface of a transactional provider (SendGrid, Mailgun, AWS
  SES, Resend, Postmark, etc.). Whichever provider you pick, use their SMTP credentials, not an
  API-only integration.

**Storage:** `STORAGE_PROVIDER=local` (default, writes under `backend/storage/local/`) or `s3`
(set the `S3_*` variables — a real S3-compatible implementation exists but is unexercised without
real bucket credentials).

## Running backend checks

```bash
cd backend
uv run ruff check --fix .      # lint
uv run mypy .                  # type check
uv run pytest -q               # full test suite
```

## Running frontend checks

```bash
cd frontend
npx tsc --noEmit                # type check
npm run lint                    # eslint
npm run build                   # production build (also catches issues npx tsc alone won't)
```

## Database migrations

```bash
cd backend
uv run alembic upgrade head        # apply all pending migrations
uv run alembic downgrade -1        # roll back the most recent migration
uv run alembic current             # show the currently applied revision
uv run alembic revision --autogenerate -m "describe the change"   # after editing models
```

Every migration in this repo is written to be reversible (`upgrade`/`downgrade` both work,
including Postgres ENUM types, which don't autogenerate a clean rollback by default).

## Project layout

```
backend/
  app/            framework-level code: config, DB session, core abstractions (AI provider
                   interface, storage interface, CRUD base classes), auth/permission dependencies
  features/       one folder per domain (profiles, education, experience, resumes, ai, jobs,
                   companion, etc.) — each owns its models/schemas/repository/service/router/tests
  alembic/         migrations
  templates/       Jinja2 templates rendered to PDF (resumes)
frontend/
  app/            Next.js routes
  features/       one folder per domain, mirroring the backend
docker/           docker-compose.yml + Dockerfiles
```

## Troubleshooting

- **Port already in use (5432/6379/8000/3000):** something else on the machine is bound to that
  port. Check with `ss -ltnp` and stop the conflicting process, or change the host-side port
  mapping in `docker/docker-compose.yml`.
- **Docker commands hang / can't connect to the daemon:** confirm the active Docker context is the
  one with a running engine — `docker context ls`, then `docker context use <name>`.
- **Frontend changes to a mutation inside a `Suspense` boundary don't appear to re-render:** a
  known `next dev`/Turbopack-only defect. Verify with a production build
  (`npm run build && npm run start -- -p 3000`) before concluding it's a real bug.
