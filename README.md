# 🇩🇪 Germany Company Scraper — Scraping Panel

Web panel to scrape German companies across selected cities and categories, stream
results in realtime over WebSocket, deduplicate in memory, and export to Excel/PDF.

> **No CRM. No database. No Docker. No Redis. No Celery. No OpenAI.**
> Deterministic scraping only — Camoufox + Playwright + Python + DOM + JSON-LD + Regex.

## Architecture

```
VERCEL (Frontend)
  Next.js 14 · React 18 · TypeScript · Tailwind · TanStack Query · WebSocket
        │  REST + WebSocket
        ▼
VERİDYEN SUNUCUSU (Backend)
  FastAPI
    ├─ JobService / JobQueue   (in-memory, concurrency-limited, asyncio)
    ├─ ScrapingManager
    │   └─ SourceAdapter (DirectorySource, WebsiteSource)
    │       └─ CamoufoxEngine ── BrowserManager (context pooling)
    │           └─ JSON-LD → meta → DOM → regex extraction
    │               → Normalize → Validate → Deduplicate(merge) → Store
    ├─ JobStore (in-memory results + dedup keys per job)
    ├─ EventService (in-memory event log + WebSocket broadcast)
    └─ ExportService (openpyxl → Excel, WeasyPrint → PDF)
```

All job state — results, dedup indexes, counters, events — lives in **process
memory**. Page refresh or server restart loses it (accepted for this version).
There is no persistence layer.

## Tech Stack

| Layer    | Technology |
|----------|------------|
| Backend  | Python 3.12, FastAPI, Pydantic v2, asyncio |
| Scraping | Camoufox, Playwright, BeautifulSoup/lxml, httpx |
| Storage  | In-memory job state only (no database) |
| Export   | openpyxl (Excel), WeasyPrint (PDF) |
| Realtime | WebSocket |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind, TanStack Query |
| Deploy   | Frontend → Vercel, Backend → existing Veridyen server |

## Project Layout

```
backend/
  app/
    api/            # FastAPI routers (scrape, auth) + WebSocket
    core/           # config, logging, security, schemas, catalog, job_store
    scraper/
      engines/      # camoufox_engine, browser_manager
      sources/      # base, directory, website, registry
      extractors/   # jsonld, company_data, pages
      normalizers/  # normalizer, pipeline
      deduplication/# in-memory deduplicator + merge
      validators/   # candidate_validator, category_validator
      scraper_manager.py
    services/       # job (service+queue), event, export
    tests/          # unit tests
frontend/
  app/              # Next.js app router (German UI)
  components/       # layout, common
  hooks/            # useJobSocket (realtime)
  lib/api/          # API client + types
```

## Getting Started

### Backend (Veridyen server)

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m camoufox fetch        # download Camoufox browser (once)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Default login: `admin@example.com` / `admin123` (seeded in memory on first use).

### Frontend (local dev)

```bash
cd frontend
cp .env.example .env.local       # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

## Realtime Scraping Flow

1. User selects cities + categories, clicks **"Scraping starten"**.
2. Frontend opens a single `POST /api/scrape/jobs` request that returns a
   `text/event-stream` (SSE). The job runs **inside that one request**.
3. `ScrapingManager` loops over each city × category combination:
   - source `search()` → company URLs
   - for each URL (bounded concurrency): `extract_company()` → normalize → validate → dedupe/merge → store in memory
   - emits an SSE event for every step (search, found, saved, duplicate, merged, error).
4. The panel renders the live activity log and a results table that grows in realtime from the SSE stream.
5. On completion, **"Excel herunterladen"** and **"PDF herunterladen"** POST the collected results back and download the generated file.

Duplicates are detected per job by: normalized website → normalized phone → email → normalized name + city.
Missing fields on a matched company are filled in instead of creating a new row.

## API (summary)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET  | `/api/cities` | List cities (static catalog) |
| GET  | `/api/categories` | List categories (static catalog) |
| GET  | `/api/dashboard/stats` | Dashboard counters (in-memory jobs) |
| POST | `/api/scrape/jobs` | Create + start a scrape job |
| GET  | `/api/scrape/jobs` | List in-memory jobs |
| GET  | `/api/scrape/jobs/{id}` | Job detail |
| POST | `/api/scrape/jobs/{id}/cancel` | Cancel a job |
| GET  | `/api/scrape/jobs/{id}/companies` | Companies of a job (filterable) |
| GET  | `/api/scrape/jobs/{id}/events` | Event log of a job |
| POST | `/api/scrape/jobs/{id}/export/excel` | Export to Excel |
| POST | `/api/scrape/jobs/{id}/export/pdf` | Export to PDF |
| GET  | `/api/exports/{filename}` | Download an export |
| WS   | `/ws/jobs/{id}` | Realtime events |
| POST | `/api/auth/register` / `/api/auth/login` | In-memory auth (JWT) |

## Configuration (`.env`)

```
CAMOUFOX_HEADLESS=true
CAMOUFOX_HUMANIZE=false
MAX_CONCURRENT_JOBS=2
MAX_CONCURRENT_PAGES=4
PAGE_TIMEOUT=30000
NAVIGATION_TIMEOUT=30000
MAX_RETRIES=2
REQUEST_DELAY_MS=800
MAX_COMPANIES_PER_CITY_CATEGORY=0   # 0 = unlimited
EXPORT_DIR=./exports
SECRET_KEY=change-me-in-production
ALLOWED_ORIGINS=*
DEFAULT_USER_EMAIL=admin@example.com
DEFAULT_USER_PASSWORD=admin123
```

## Testing

```bash
cd backend
pytest            # unit tests — no database, no network, no real scraping
ruff check app    # lint
```

## Extending with a new source

```python
# backend/app/scraper/sources/my_source.py
from app.scraper.sources.base import BaseSource

class MySource(BaseSource):
    name = "my_source"
    async def search(self, city, category, engine, max_results=0): ...
    async def extract_company(self, url, engine, city="", category=""): ...
    def supports(self, city, category): return True
    def get_search_query(self, city, category): return f"{category} {city}"
```

Then register it: `registry.register(MySource())` in
`backend/app/scraper/sources/__init__.py`.

## Deploy (single Vercel Pro deployment)

One Vercel project serves both frontend and backend on a single domain
(`https://germany-scraper.vercel.app`) using **Vercel Services**:

- `frontend/` → Next.js service (all page routes)
- `backend/` → FastAPI service (`api.index:app`), reached via `/api/*`
- Root `vercel.json` rewrites `/api/(.*)` to the backend service and `/(.*)` to the frontend.
- **Fluid Compute** is enabled; the backend function has `maxDuration: 1800` (30 min).

Because Functions are stateless, each scraping job runs **inside a single request**
and streams events back over **SSE** (`text/event-stream`) — no WebSocket, no
background worker, no cross-request polling. The frontend reads the stream with
`fetch` + `ReadableStream`.

### Deployment

```bash
# from repo root
vercel link --yes --project germany-scraper
vercel env add ADMIN_USERNAME production
vercel env add ADMIN_PASSWORD production
vercel env add AUTH_SECRET production
vercel env add VERCEL_SUPPORT_LARGE_FUNCTIONS production
vercel deploy --prod --yes
```

The build step (`backend/build.py`) runs `python -m camoufox fetch` with
`XDG_CACHE_HOME=./.camoufox_cache`, so the ~600 MB browser is bundled into the
backend function (requires **Large Functions** — set
`VERCEL_SUPPORT_LARGE_FUNCTIONS=1`). At runtime the browser is **read** from the
bundled cache (read-only filesystem) — nothing is copied to `/tmp`.

### Scraping strategy (HTTP-first)

1. `HttpEngine` fetches each URL over plain HTTP (httpx, retries, UA, redirects).
2. If the page is a bot challenge, empty, or returns an error status, it falls
   back to **Camoufox** (real browser).
3. In the browser, JavaScript stays **enabled**, but images, video, fonts,
   analytics and tracking/advertisement requests are **blocked** via request
   interception — the page is rendered, not the media.
4. A single browser is launched per invocation and reused via a context pool
   (no per-company browser restart).

### Local development

Backend:
```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m camoufox fetch
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Default login: `admin` / `admin123` (from `ADMIN_USERNAME`/`ADMIN_PASSWORD` env).

> **Realtime model:** results are streamed live over SSE while the job runs inside
> its own request. There is no persistent job history — refresh loses results
> (accepted by design). Export is stateless: the frontend posts the collected
> companies back to `/api/scrape/export/{excel,pdf}` and downloads the file.

## Deliberately NOT included

PostgreSQL, MySQL, MongoDB, Redis, Celery, RabbitMQ, Docker, Kubernetes,
Elasticsearch, Kafka, OpenAI, LLM. This project is a scraping panel only.