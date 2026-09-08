export interface City {
  id: number;
  name: string;
  slug: string;
  state: string;
  active: boolean;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  group: string;
  description: string | null;
  search_terms: string[];
  keywords: string[];
  active: boolean;
}

export interface Company {
  id: number;
  name: string;
  phone: string | null;
  email: string | null;
  website: string | null;
  street: string | null;
  house_number: string | null;
  postal_code: string | null;
  city: string | null;
  state: string | null;
  category: string | null;
  source: string | null;
  source_url: string | null;
  job_id: number | null;
  phone_verified: boolean;
  email_verified: boolean;
  website_verified: boolean;
}

export interface ScrapeJob {
  id: number;
  status: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  city_count: number;
  category_count: number;
  total_found: number;
  total_added: number;
  total_duplicates: number;
  total_merged: number;
  total_failed: number;
}

export interface ScrapeEvent {
  id: number;
  job_id: number;
  timestamp: string;
  event_type: string;
  city: string | null;
  category: string | null;
  company_name: string | null;
  message: string | null;
  progress: number;
}

export interface DashboardStats {
  total_companies: number;
  today_found: number;
  active_scrapes: number;
  success_rate: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiRequest<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error((body as any).detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

export function wsUrl(jobId: number | string): string {
  const ws = API_URL.replace(/^http/, "ws");
  return `${ws}/ws/jobs/${jobId}`;
}

export function downloadUrl(path: string): string {
  return `${API_URL}${path}`;
}

export const getCities = () => apiRequest<City[]>("/api/cities");
export const getCategories = () => apiRequest<Category[]>("/api/categories");
export const getDashboardStats = () => apiRequest<DashboardStats>("/api/dashboard/stats");

export const createJob = (data: {
  city_ids: number[];
  category_ids: number[];
  max_results?: number;
}) => apiRequest<ScrapeJob>("/api/scrape/jobs", { method: "POST", body: JSON.stringify(data) });

export const getJobs = () => apiRequest<ScrapeJob[]>("/api/scrape/jobs");
export const getJob = (id: number) => apiRequest<ScrapeJob>(`/api/scrape/jobs/${id}`);
export const cancelJob = (id: number) => apiRequest(`/api/scrape/jobs/${id}/cancel`, { method: "POST" });

export const getJobCompanies = (
  jobId: number,
  filters?: { hasEmail?: boolean; hasPhone?: boolean; q?: string }
) => {
  const params = new URLSearchParams();
  if (filters?.hasEmail) params.set("has_email", "true");
  if (filters?.hasPhone) params.set("has_phone", "true");
  if (filters?.q) params.set("q", filters.q);
  const qs = params.toString();
  return apiRequest<Company[]>(`/api/scrape/jobs/${jobId}/companies${qs ? `?${qs}` : ""}`);
};

export const getJobEvents = (jobId: number) => apiRequest<ScrapeEvent[]>(`/api/scrape/jobs/${jobId}/events`);

export const exportExcel = (jobId: number) =>
  apiRequest<{ status: string; file_url: string; count: number }>(
    `/api/scrape/jobs/${jobId}/export/excel`,
    { method: "POST" }
  );
export const exportPdf = (jobId: number) =>
  apiRequest<{ status: string; file_url: string; count: number }>(
    `/api/scrape/jobs/${jobId}/export/pdf`,
    { method: "POST" }
  );

export const login = (email: string, password: string) =>
  apiRequest<{ access_token: string; token_type: string }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

export const register = (email: string, password: string) =>
  apiRequest<{ access_token: string; token_type: string }>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
