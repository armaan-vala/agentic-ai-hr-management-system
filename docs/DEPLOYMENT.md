# Deployment Guide

Frontend → **Vercel** · Backend → **Render** (Docker) · DB/Auth → **Supabase** (already set up)
· Keep-alive → **GitHub Actions cron**.

## Order
1. Deploy **backend** to Render (get its URL).
2. Deploy **frontend** to Vercel (point it at the backend URL).
3. Set backend `FRONTEND_ORIGIN` to the Vercel URL.
4. Update Google OAuth redirect URIs to the production URLs.
5. Turn on the keep-alive cron.

---

## 1. Backend on Render
1. Push repo to GitHub (done).
2. Render → **New → Blueprint** → pick this repo → it reads `backend/render.yaml`.
3. Set these env vars (Dashboard → Environment) — values from your local `backend/.env`:
   - `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SECRET_KEY`
   - `GROQ_API_KEYS`, `APP_SECRET`, `TOKEN_ENCRYPTION_KEY`
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI` = `https://<backend>.onrender.com/google/callback`
   - `GOOGLE_POST_CONNECT_REDIRECT` = `https://<frontend>.vercel.app/settings?google=connected`
   - `FRONTEND_ORIGIN` = `https://<frontend>.vercel.app` (fill after step 2)
4. Deploy. Migrations run automatically on startup. Health check: `/health`.

## 2. Frontend on Vercel
1. Vercel → **New Project** → import the repo.
2. **Root Directory** = `frontend`. Framework preset: **Vite** (auto).
3. Env vars:
   - `VITE_SUPABASE_URL` = your Supabase URL
   - `VITE_SUPABASE_ANON_KEY` = `sb_publishable_...`
   - `VITE_API_URL` = `https://<backend>.onrender.com`
4. Deploy → note the `https://<frontend>.vercel.app` URL.

## 3. Wire them together
- In Render, set `FRONTEND_ORIGIN` to the Vercel URL → redeploy (or it picks up on next deploy).

## 4. Google OAuth (production)
In Google Cloud → Credentials → your OAuth client → **Authorized redirect URIs**, add:
`https://<backend>.onrender.com/google/callback`

## 5. Keep-alive
GitHub → repo → Settings → Secrets and variables → **Actions → Variables** →
add `BACKEND_HEALTH_URL` = `https://<backend>.onrender.com/health`.
The `.github/workflows/keep-alive.yml` cron pings it every 12 min so the free tier never sleeps.

## Supabase note
Auth → Providers → Email → decide on **"Confirm email"** (off = instant signup for testing).
