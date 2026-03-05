# Louder World

Louder World is a Sydney (Australia) event listing site.

It consists of:
- A Python scraper that collects events from public sources and upserts them into MongoDB.
- A Django REST API (plus Celery background jobs) that reads/writes MongoDB.
- A Next.js frontend that displays events, supports a “Get Tickets” email/consent flow, and an admin dashboard protected by Google OAuth.

This repository is a monorepo:
- `events-frontend/` — Next.js (App Router) UI + NextAuth Google OAuth
- `events-api/` — Django REST API + Celery tasks (scraping scheduler, inactive marking, optional recommendations)
- `event-scraper/` — Python scraper package (can be run standalone or via the API’s Celery tasks)

For deployment (Vercel + Render + MongoDB Atlas) see `DEPLOYMENT.md`.

## Architecture (high level)

1) **Scraper** fetches and parses multiple source sites and writes/upserts into MongoDB (`events` collection).

2) **API** exposes the Mongo-backed data via REST endpoints and also writes subscriptions (`subscriptions` collection).

3) **Frontend** calls the API to show event listings, posts subscriptions on “Get Tickets”, and provides an admin dashboard that proxies secure “import” actions.

## Prerequisites

- Docker Desktop (recommended for local MongoDB + Redis)
- Python 3.10+ (Django 5.2 requires modern Python)
- Node.js (LTS) + npm

Ports used by default:
- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- MongoDB: `mongodb://localhost:27017`
- Redis: `redis://localhost:6379`

## Quickstart (local dev)

### 1) Start MongoDB + Redis (Docker)

From the repo root:

```bash
cd event-scraper
docker compose up -d
```

This starts:
- MongoDB on `localhost:27017`
- Redis on `localhost:6379`

### 2) Start the Django API (port 8000)

In a new terminal:

```bash
cd events-api

# Windows PowerShell example venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Optional: set environment variables (see below), then
python manage.py migrate
python manage.py runserver 8000
```

The API base URL is:

`http://localhost:8000/api`

### 3) Run the scraper once (optional, to populate events)

Option A — via Django management command (uses the same code as the Celery task):

```bash
cd events-api
python manage.py run_scraper
```

Option B — run the scraper module directly:

```bash
cd event-scraper
python -m scraper.main
```

### 4) Start Celery (optional, for scheduled scraping)

If you want the scraper to run periodically, run both a worker and beat.

Worker (Windows note: use `--pool=solo`):

```bash
cd events-api
celery -A events_api worker --loglevel=info --pool=solo
```

Beat (scheduler):

```bash
cd events-api
celery -A events_api beat --loglevel=info
```

The beat schedule includes:
- `events.tasks.run_scraper_task` every ~30 minutes
- `events.tasks.mark_inactive_task` daily
- `events.tasks.rebuild_faiss_index` daily (only meaningful if recommendations deps/index are set up)

### 5) Start the Next.js frontend (port 3000)

In a new terminal:

```bash
cd events-frontend
npm install
npm run dev
```

Open:
- Public listing: `http://localhost:3000/`
- Admin dashboard (Google sign-in): `http://localhost:3000/dashboard`

## Environment variables

This repo uses environment variables rather than committed secrets.

### Backend (Django) — `events-api/`

You can set these in your shell or in a local `.env` file inside `events-api/`.

Required for normal local running:

```bash
DJANGO_SECRET=dev-secret-change-me
DJANGO_DEBUG=1

MONGO_URI=mongodb://localhost:27017
MONGO_DB=events_db

REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Used to protect the import endpoint
ADMIN_API_TOKEN=change-me
```

Optional (recommendations/index):

```bash
EMBED_MODEL=all-MiniLM-L6-v2
FAISS_INDEX_DIR=faiss_index
```

### Frontend (Next.js) — `events-frontend/`

Create `events-frontend/.env.local`:

```bash
# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-change-me

# Google OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# API base URL (note: frontend expects the /api prefix)
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_PAGE_SIZE=12

# Must match ADMIN_API_TOKEN on the backend
NEXT_PRIVATE_ADMIN_TOKEN=change-me
```

Google OAuth redirect URI for local dev:

`http://localhost:3000/api/auth/callback/google`

## API endpoints (backend)

Base: `http://localhost:8000/api`

- `GET /events/`

  - Query params: `q`, `city`, `status`, `from`, `to`, `page`, `page_size`
- `GET /events/<event_id>/`
- `POST /subscriptions/` — body: `{ "event_id": "...", "email": "...", "consent": true }`
- `POST /admin/import/<event_id>/`

  - Requires `X-Admin-Token: <ADMIN_API_TOKEN>`
  - Optional: `X-User-Email: user@example.com`
  - Body: `{ "notes": "optional" }`
- `POST /recommendations/` (optional)

  - Body: `{ "type": "by_event", "event_id": "...", "k": 6 }` or `{ "type": "by_user", "preferences": "...", "k": 6 }`

## Recommendations (optional)

The recommendations endpoint depends on ML packages.

1) Install optional deps:

```bash
cd events-api
pip install -r requirements.txt -r requirements-ml.txt
```

2) Build the index (writes files in `events-api/faiss_index/`):

```bash
cd events-api
python scripts/build_index.py
```

If FAISS is not installed, the project falls back to `embeddings.npy` similarity.

## Deployment

See `DEPLOYMENT.md` for:
- MongoDB Atlas setup
- Backend deployment on Render (Gunicorn + optional Celery worker/beat)
- Frontend deployment on Vercel
- Required production environment variables

