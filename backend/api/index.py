"""Vercel serverless entrypoint for the FastAPI backend.

Note: Vercel serverless functions are stateless and short-lived. The scraping
pipeline (Camoufox + long-running jobs + WebSocket) requires a persistent
process and CANNOT run here. This entrypoint serves the static API surface
(cities, categories, auth, job metadata, exports) so the panel UI works.

Run the full backend with:  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from app.main import app