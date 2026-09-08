from __future__ import annotations

from typing import Annotated

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, NoDecode


def _split_csv(value):
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    APP_NAME: str = "Germany Company Scraper"

    # --- Scraping / HTTP-first ---
    HTTP_TIMEOUT: float = 15.0
    HTTP_MAX_RETRIES: int = 2
    HTTP_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    CAMOUFOX_HEADLESS: bool = True
    CAMOUFOX_HUMANIZE: bool = False
    MAX_CONCURRENT_JOBS: int = 1
    MAX_CONCURRENT_PAGES: int = 2
    PAGE_TIMEOUT: int = 30000
    NAVIGATION_TIMEOUT: int = 30000
    MAX_RETRIES: int = 2
    REQUEST_DELAY_MS: int = 800
    MAX_COMPANIES_PER_CITY_CATEGORY: int = 0

    # --- Auth (DB-less, from env) ---
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    AUTH_SECRET: str = "change-me-in-production"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Backward-compatible aliases (DEFAULT_USER_EMAIL/PASSWORD, SECRET_KEY)
    DEFAULT_USER_EMAIL: str = "admin@example.com"
    DEFAULT_USER_PASSWORD: str = "admin123"

    ALLOWED_ORIGINS: Annotated[list[str], NoDecode, BeforeValidator(_split_csv)] = ["*"]

    EXPORT_DIR: str = "/tmp/exports"

    # --- Supabase (optional persistence: dedup + history) ---
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_SERVICE_KEY)

    @property
    def effective_secret_key(self) -> str:
        return self.AUTH_SECRET or self.SECRET_KEY or "change-me-in-production"


settings = Settings()
