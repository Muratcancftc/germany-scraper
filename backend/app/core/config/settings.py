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
    CAMOUFOX_HEADLESS: bool = True
    CAMOUFOX_HUMANIZE: bool = False
    MAX_CONCURRENT_JOBS: int = 2
    MAX_CONCURRENT_PAGES: int = 4
    PAGE_TIMEOUT: int = 30000
    NAVIGATION_TIMEOUT: int = 30000
    MAX_RETRIES: int = 2
    REQUEST_DELAY_MS: int = 800
    MAX_COMPANIES_PER_CITY_CATEGORY: int = 0
    EXPORT_DIR: str = "./exports"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode, BeforeValidator(_split_csv)] = ["*"]
    DEFAULT_USER_EMAIL: str = "admin@example.com"
    DEFAULT_USER_PASSWORD: str = "admin123"

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
