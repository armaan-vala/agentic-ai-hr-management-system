# TalentOS — Agentic HRMS

AI-powered HR Management System with a **truly agentic** assistant (reason → act → observe loop,
not fixed if-else), multi-tenant, built to be **reliably deployable** on free/permanent tiers.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React + Vite + TypeScript + Tailwind + shadcn/ui (amber `#f5b942`, light theme) |
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0 async, Alembic |
| DB / Auth | Supabase (Postgres + pgvector + Auth) |
| LLM | Groq (multi-key rotation) |
| Jobs | APScheduler (in-process) — no Redis |
| Deploy | Frontend → Vercel · Backend → Render/Railway · Keep-alive → GitHub Actions cron |

## Project layout

```
backend/    FastAPI app, agent runtime, Groq key pool, DB models, Alembic
frontend/   Vite React app, theme, Supabase client
.github/    keep-alive cron workflow
```

## Local dev

```bash
# Backend
cd backend
cp .env.example .env         # fill values
docker compose up --build    # (from repo root) OR run uvicorn in a 3.12 venv

# Frontend
cd frontend
npm install
npm run dev
```

## Versioning

Releases are git tags: `v0.1.0`, `v0.2.0`, ... See `docs/GIT_GUIDE.md`.
