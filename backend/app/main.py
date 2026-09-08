from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.scrape import router as scrape_router
from app.core.config import settings
from app.core.logging.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.APP_NAME)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape_router)
app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "germany-scraper"}


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "germany-scraper",
        "message": "Backend API çalışıyor. Panel: frontend (npm run dev) — API dokümanı: /docs",
        "endpoints": ["/api/cities", "/api/categories", "/api/auth/login", "/api/scrape/jobs", "/docs"],
    }
