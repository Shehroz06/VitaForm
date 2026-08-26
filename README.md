# VitraForm

Build one structured profile — your education, experience, projects, skills, and everything
else you've done — and let AI generate the specific document a moment calls for: a
job-targeted resume, a cover letter, a LinkedIn "About" section. On demand, reproducibly,
without ever retyping your career from scratch.

## The idea

Most tools ask you to write a resume, then another resume for the next job, then a cover
letter, then rewrite your LinkedIn bio — the same facts, retyped over and over, drifting out
of sync every time.

VitraForm inverts that. **Your profile is permanent. Documents are temporary, generated
output.** Add an experience once; it's available to every resume, cover letter, and bio you
generate afterward, tailored differently each time to fit the job description in front of you.

The database is always the source of truth — the AI only selects, ranks, and arranges facts
that are actually in your profile, and writes the connective prose around them. It never
invents an experience, a project, or a skill you didn't add. If something's missing, the
output leaves it out rather than making it up.

You can also bootstrap a profile by uploading an existing resume as a PDF — the AI extracts
and classifies what it finds, but nothing is written until you've reviewed and confirmed it.

## Features

**Structured profile** — education, experience, projects, skills, certifications,
achievements, awards, research, patents, hackathons, competitions, volunteer work, leadership
roles, organizations, languages, references, interests, and a portfolio. Every section has
full CRUD, independent of any document.

**AI-generated documents** — a job-targeted resume (with version history and one-page
autofit), a cover letter, and a LinkedIn "About" section, each built from your real profile
data and a job description you provide.

**CV import** — upload a PDF resume; the AI reads it (text and layout) and proposes
structured profile entries for you to review, edit, and accept individually. Nothing saves
without your confirmation.

**Job tracking & ATS scoring** — save job descriptions, get an AI fit analysis, and score a
generated resume against a job posting's likely ATS keyword matching.

**Provider-agnostic AI** — Gemini, Groq, OpenRouter, OpenAI, or Anthropic, swappable via a
single config value. Automatic fallback if your primary provider is unavailable.

**PDF export** — resumes render to real, downloadable PDFs from multiple templates.

## Tech stack

| Layer | Stack |
|---|---|
| Backend | FastAPI, SQLAlchemy, Alembic, PostgreSQL |
| Frontend | Next.js , TypeScript, Tailwind, shadcn/ui, TanStack Query |
| AI | Gemini / Groq / OpenRouter / OpenAI / Anthropic — provider-agnostic |
| Auth | JWT access tokens + HttpOnly refresh cookie, Argon2 password hashing |

---

## Getting started

**Prerequisites:** Docker + Docker Compose. (For running tooling outside a container: Python
3.13 + [`uv`](https://docs.astral.sh/uv/) for the backend, Node 22+ for the frontend.)

```bash
# 1. Backend environment
cp backend/.env.example backend/.env
# then set at least one AI provider key (see "AI providers" below) — everything
# else has a working default.

# 2. Frontend environment
cp frontend/.env.example frontend/.env

# 3. Boot the full stack (Postgres + Redis + backend + frontend)
docker compose -f docker/docker-compose.yml up -d --build

# 4. Apply database migrations
cd backend && uv run alembic upgrade head
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (`GET /api/v1/health` should return `{"success": true, ...}`)
- API docs: http://localhost:8000/docs

Tear down with `docker compose -f docker/docker-compose.yml down` (add `-v` to also drop the
Postgres volume).

### AI providers

At least one is needed for resume/cover-letter/LinkedIn generation and CV import; everything
else (profile CRUD, manual resume export, job/ATS analysis) works without any AI key.

- `AI_DEFAULT_PROVIDER` picks the primary provider; `AI_FALLBACK_PROVIDERS` is an ordered list
  tried if the default fails or isn't configured.
- Supported: `gemini`, `groq`, `openrouter`, `openai`, `anthropic`. Set the matching
  `<PROVIDER>_API_KEY`. Gemini's free tier (https://aistudio.google.com/apikey) and Groq's
  free tier (https://console.groq.com/keys) are both good, zero-cost starting points.
- Switching providers is a config change only — no code changes required.

### Email (OTP / verification / password reset)

- `EMAIL_PROVIDER=console` (default) — emails are logged to the backend container's stdout
  instead of being sent. Fine for local development.
- `EMAIL_PROVIDER=smtp` — sends real email via any SMTP endpoint (a relay, or a transactional
  provider's SMTP interface — SendGrid, Mailgun, SES, Resend, Postmark, etc).

---

## Project layout

```
backend/
  app/            framework-level code: config, DB session, core abstractions (AI provider
                   interface, storage interface, CRUD base classes), auth/permission dependencies
  features/       one folder per domain (profiles, education, experience, resumes, ai, jobs,
                   companion, cv_import, etc.) — each owns its models/schemas/repository/service/router
  alembic/         migrations
  templates/       Jinja2 templates rendered to PDF (resumes)
frontend/
  app/            Next.js routes
  features/       one folder per domain, mirroring the backend
docker/           docker-compose.yml + Dockerfiles
```

## Roadmap

AI interview coaching, application tracking, public portfolio pages, a recruiter dashboard,
university/scholarship application support, career analytics, and a plugin system are on the
long-term roadmap.

## License

Educational use — see [LICENSE](LICENSE).
