# Louder World — Submission Report

Date: 2026-02-06

## Overview
This project is a Sydney (Australia) event listing website built with open-source tools. It automatically scrapes events from multiple public event websites, stores them in a database, exposes them through an API, and displays them in a minimal UI. It also includes Google OAuth login and an admin dashboard for importing events into the platform.

## Tech Stack
- Frontend: Next.js (App Router), React
- Auth: NextAuth (Google OAuth)
- Backend API: Django + Django REST Framework
- Database: MongoDB (events + subscriptions)
- Background jobs: Celery + Redis
- Scraper: Python + requests + BeautifulSoup

## Assignment 1 (Mandatory) — Requirement Checklist

### A) Event Scraping + Auto Updates
- Multiple sources for Sydney: Implemented (City of Sydney “What’s On”, Sydney.com Events)
- Stored fields (where available):
  - Title: ✅
  - Date/time: ✅ (best-effort parsing)
  - Venue/location: ✅ (venue string, may include address)
  - City: ✅ (`city` field, default “Sydney”)
  - Description/summary: ✅
  - Image/poster URL: ✅ (best-effort)
  - Source website name: ✅ (`source_name`)
  - Original event URL: ✅ (`source_url`)
  - Last scraped time: ✅ (`last_scraped_at`)
  - Category/tags: ⚠️ best-effort (`tags` present for some sources)
- Auto updates:
  - Detect new events: ✅ (insert)
  - Detect updated events: ✅ (checksum change → `updated`)
  - Detect inactive events: ✅ (mark `inactive` after cutoff)
  - Runs automatically: ✅ (Celery Beat schedule)

### B) Event Listing Website
- Minimal UI listing: ✅
- Event card shows: name, date/time, venue, description, source, GET TICKETS CTA: ✅
- GET TICKETS flow:
  - Email prompt + opt-in checkbox: ✅
  - Save email + consent + event reference: ✅ (`/api/subscriptions/`)
  - Redirect to original event URL: ✅

### C) Google OAuth + Dashboard
- Google OAuth sign-in: ✅
- Only logged-in users can access dashboard: ✅ (NextAuth middleware protects `/dashboard`)
- Dashboard filters: ✅ city (default Sydney), keyword, date range
- Dashboard views: ✅ table view + preview panel
- Actions: ✅ per-event “Import”
  - Sets `imported` status: ✅
  - Stores `importedAt`, `importedBy`, optional `importNotes`: ✅
- Status tags demonstrated: ✅ `new`, `updated`, `inactive`, `imported`

## How to Run Locally

### 1) Start MongoDB + Redis
Option A: Docker Compose (recommended)
- From `event-scraper/`, run Docker Compose to start services.

Option B: Run Redis separately
- Redis is configured in backend via `REDIS_URL`.

### 2) Start Django API
- From `events-api/`:
  - Run migrations/checks
  - Start server on port 8000

### 3) Start Celery Worker + Beat
- Use `--pool=solo` on Windows.

### 4) Run Next.js Frontend
- From `events-frontend/`:
  - Install deps, start dev server.

## Deployment Notes (Live Link)
For a live review link:
See DEPLOYMENT.md for step-by-step deployment:
- Frontend: Vercel
- Backend: Render (web + Celery worker + Celery beat)
- Database: MongoDB Atlas
Important: rotate OAuth secrets and admin token for any public deployment.
