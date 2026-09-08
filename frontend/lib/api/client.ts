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
  payload?: { company?: Partial<Company> };
}

export interface DashboardStats {
  total_companies: number;
  today_found: number;
  active_scrapes: number;
  success_rate: number;
}

// Same-origin: frontend and backend live in the same Vercel deployment.
// For local dev, NEXT_PUBLIC_API_URL can point at the local backend.
const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("token");
}

function authHeaders(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiRequest<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...authHeaders() },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error((body as any).detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

/**
 * Start a scraping job and stream its SSE events.
 * Vercel Functions are stateless, so the job runs inside this one request.
 * Returns an async generator of parsed event objects.
 */
export async function* streamJob(data: {
  city_ids: number[];
  category_ids: number[];
  max_results?: number;
}): AsyncGenerator<ScrapeEvent> {
  const response = await fetch(`${API_URL}/api/scrape/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  });
  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => ({}));
    throw new Error((body as any).detail || `Request failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let sepIndex: number;
      while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);
        const dataLine = frame
          .split("\n")
          .find((l) => l.startsWith("data: "));
        if (dataLine) {
          try {
            const event = JSON.parse(dataLine.slice(6));
            yield event as ScrapeEvent;
          } catch {
            // skip malformed frames
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export function downloadBlobUrl(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function exportExcel(companies: Partial<Company>[]): Promise<void> {
  const response = await fetch(`${API_URL}/api/scrape/export/excel`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ companies }),
  });
  if (!response.ok) throw new Error("Export fehlgeschlagen");
  const blob = await response.blob();
  downloadBlobUrl(blob, "scraping_ergebnisse.xlsx");
}

export async function exportPdf(companies: Partial<Company>[]): Promise<void> {
  const response = await fetch(`${API_URL}/api/scrape/export/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ companies }),
  });
  if (!response.ok) throw new Error("Export fehlgeschlagen");
  const blob = await response.blob();
  downloadBlobUrl(blob, "scraping_ergebnisse.pdf");
}

export const getCities = () => apiRequest<City[]>("/api/cities");
export const getCategories = () => apiRequest<Category[]>("/api/categories");
export const getDashboardStats = () => apiRequest<DashboardStats>("/api/dashboard/stats");

export const login = (username: string, password: string) =>
  apiRequest<{ access_token: string; token_type: string }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });