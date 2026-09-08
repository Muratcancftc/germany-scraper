"""Vercel serverless entrypoint for the FastAPI backend.

Runs on Vercel Pro + Fluid Compute. maxDuration is set to 30 minutes so a
scraping job can run inside a single request and stream its events back over
SSE. The Camoufox browser is downloaded at build time (build.py) into
.camoufox_cache and copied to /tmp at runtime by browser_manager.

Locally, run the full backend with:  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import os

# Vercel sets this in production. Browser data dir must be writable -> /tmp.
os.environ.setdefault("VERCEL", "1" if os.environ.get("VERCEL_ENV") else "")

from app.main import app  # noqa: E402,F401

