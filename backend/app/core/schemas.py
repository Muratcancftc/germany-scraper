"""Shared Pydantic request/response schemas. DB-free — they model the in-memory
job/company state rather than any ORM row."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class CityResponse(BaseModel):
    id: int
    name: str
    slug: str
    state: str
    active: bool = True


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    group: str
    description: str | None = None
    search_terms: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    active: bool = True


class CompanyResponse(BaseModel):
    id: int
    name: str
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    street: str | None = None
    house_number: str | None = None
    postal_code: str | None = None
    city: str | None = None
    state: str | None = None
    country: str = "DE"
    category: str | None = None
    source: str | None = None
    source_url: str | None = None
    job_id: int | None = None
    phone_verified: bool = False
    email_verified: bool = False
    website_verified: bool = False


class ScrapeJobResponse(BaseModel):
    id: int
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    city_count: int
    category_count: int
    total_found: int
    total_added: int
    total_duplicates: int
    total_merged: int
    total_failed: int
    total_rejected: int = 0
    current: str = ""


class CreateJobRequest(BaseModel):
    city_ids: list[int] = Field(..., min_length=1)
    category_ids: list[int] = Field(..., min_length=1)
    max_results: int | None = None
    max_concurrent_pages: int | None = None


class ScrapeEventResponse(BaseModel):
    id: int
    job_id: int
    timestamp: str
    event_type: str
    city: str | None = None
    category: str | None = None
    company_name: str | None = None
    message: str | None = None
    progress: float = 0.0


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DashboardStats(BaseModel):
    total_companies: int
    today_found: int
    active_scrapes: int
    success_rate: float
