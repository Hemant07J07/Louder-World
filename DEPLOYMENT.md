# Deployment (Vercel + Render + MongoDB Atlas)

This repo is a mono-repo:
- Frontend (Next.js): `events-frontend/`
- Backend (Django API + Celery): `events-api/`

Goal: produce a **live link** for review and keep secrets out of git.

## 1) MongoDB Atlas
1. Create a free (Shared) Atlas cluster.
2. Create a DB user + password.
3. Network access: allow your backend host (for quick testing you can temporarily allow `0.0.0.0/0`).
4. Copy the connection string:

`mongodb+srv://<USER>:<PASS>@cluster0.xxxx.mongodb.net/events_db?retryWrites=true&w=majority`

Environment variables you will use:
- `MONGO_URI`
- `MONGO_DB=events_db`

## 2) Deploy Django API on Render
Create a **Web Service** from the `events-api/` directory.

### Render settings
- Root Directory: `events-api`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn events_api.wsgi:application --bind 0.0.0.0:$PORT --workers 2`

### Render environment variables (backend)
- `DJANGO_SECRET` (random long string)
- `DJANGO_DEBUG=0`
- `ALLOWED_HOSTS=<your-render-hostname>` (optional; current settings allow all)
- `MONGO_URI=<atlas-connection-string>`
- `MONGO_DB=events_db`
- `ADMIN_API_TOKEN=<random token>`

If using Celery:
- `REDIS_URL=<managed redis url>`
- `CELERY_BROKER_URL=<same as REDIS_URL>`
- `CELERY_RESULT_BACKEND=<same as REDIS_URL>`

### Background workers (Celery)
Create **two Background Worker** services in Render from the same repo/root:

Worker:
- Start: `celery -A events_api worker --loglevel=info`

Beat:
- Start: `celery -A events_api beat --loglevel=info`

## 3) Deploy Next.js on Vercel
Import the repo into Vercel.

Vercel project settings:
- Root Directory: `events-frontend`

### Vercel environment variables (frontend)
- `NEXTAUTH_URL=https://<your-vercel-domain>`
- `NEXTAUTH_SECRET=<random long string>`
- `NEXT_PUBLIC_API_URL=https://<your-render-domain>/api`
- `NEXT_PUBLIC_PAGE_SIZE=12`
- `GOOGLE_CLIENT_ID=<google-oauth-web-client-id>`
- `GOOGLE_CLIENT_SECRET=<google-oauth-web-client-secret>`
- `NEXT_PRIVATE_ADMIN_TOKEN=<same value as ADMIN_API_TOKEN>`

## 4) Update Google OAuth redirect URIs
In Google Cloud Console → OAuth Client:

- Authorized JavaScript origins:
  - `https://<your-vercel-domain>`
- Authorized redirect URIs:
  - `https://<your-vercel-domain>/api/auth/callback/google`

## 5) Quick production checks
1. Visit frontend → confirm events list loads.
2. Sign in → confirm `/dashboard` redirects to Google and returns.
3. Import an event → confirm backend updates Mongo (`status=imported`, `importedAt`, `importedBy`).

## Optional: Recommendations
The recommendations endpoint is optional and can be enabled by installing ML deps.

On the backend service:
- Install: `pip install -r requirements.txt -r requirements-ml.txt`
- Build the index (one-off): `python scripts/build_index.py`
