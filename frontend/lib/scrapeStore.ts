"use client";

import { Company, ScrapeEvent, streamJob } from "@/lib/api/client";
import { upsertJob } from "@/lib/jobStore";

export interface JobStreamState {
  jobId: number | null;
  events: ScrapeEvent[];
  companies: Partial<Company>[];
  status: "idle" | "running" | "completed" | "failed" | "cancelled";
  counts: {
    found: number;
    added: number;
    duplicates: number;
    merged: number;
    failed: number;
  };
  current: string;
  error: string;
}

function companyKey(c: Partial<Company>): string {
  if (c.website) return `w:${c.website}`;
  if (c.phone) return `p:${c.phone}`;
  if (c.email) return `e:${c.email}`;
  return `n:${c.name ?? ""}`;
}

const initialState: JobStreamState = {
  jobId: null,
  events: [],
  companies: [],
  status: "idle",
  counts: { found: 0, added: 0, duplicates: 0, merged: 0, failed: 0 },
  current: "",
  error: "",
};

// Module-level singleton state. Survives page navigation so a running scrape is
// still visible when the user returns to the scraping page.
let state: JobStreamState = initialState;
const listeners = new Set<() => void>();
let activeController: AbortController | null = null;

function emit() {
  listeners.forEach((l) => l());
}

export function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function getSnapshot(): JobStreamState {
  return state;
}

function reduceEvent(prev: JobStreamState, event: ScrapeEvent): JobStreamState {
  const next: JobStreamState = {
    ...prev,
    events: [...prev.events, event],
    status: prev.status,
  };

  switch (event.event_type) {
    case "job_started":
      next.jobId = event.job_id;
      break;
    case "company_added":
      if (event.payload?.company) {
        next.companies = [event.payload.company, ...prev.companies];
        next.counts.added += 1;
      }
      break;
    case "company_merged":
      if (event.payload?.company) {
        const key = companyKey(event.payload.company);
        const idx = prev.companies.findIndex((c) => companyKey(c) === key);
        if (idx === -1) next.companies = [event.payload.company, ...prev.companies];
        else {
          const updated = [...prev.companies];
          updated[idx] = { ...updated[idx], ...event.payload.company };
          next.companies = updated;
        }
        next.counts.merged += 1;
      }
      break;
    case "company_duplicate":
      next.counts.duplicates += 1;
      break;
    case "company_failed":
      next.counts.failed += 1;
      break;
    case "job_completed":
      next.status = "completed";
      next.current = event.message || "Abgeschlossen";
      break;
    case "job_failed":
      next.status = "failed";
      next.error = event.message || "Fehlgeschlagen";
      next.current = next.error;
      break;
    case "job_cancelled":
      next.status = "cancelled";
      break;
    case "progress":
      next.current = event.message || next.current;
      break;
  }

  if (event.message) next.current = event.message;

  // Keep the shared store in sync so the Ergebnisse page shows results
  // even after leaving the scraping page.
  if (next.jobId) {
    const storedStatus: "running" | "completed" | "failed" | "cancelled" =
      next.status === "idle" ? "running" : next.status;
    upsertJob({
      jobId: next.jobId,
      status: storedStatus,
      companies: next.companies,
      events: next.events,
      counts: next.counts,
      current: next.current,
      completedAt:
        storedStatus === "completed" || storedStatus === "failed" || storedStatus === "cancelled"
          ? new Date().toISOString()
          : undefined,
    });
  }

  return next;
}

export function start(config: {
  city_ids: number[];
  category_ids: number[];
  max_results?: number;
}) {
  activeController?.abort();
  activeController = new AbortController();
  const controller = activeController;

  state = { ...initialState, status: "running" };
  emit();

  (async () => {
    try {
      for await (const event of streamJob(config, controller.signal)) {
        if (controller.signal.aborted) break;
        state = reduceEvent(state, event);
        emit();
      }
    } catch (e: any) {
      if (controller.signal.aborted) return;
      state = { ...state, status: "failed", error: e.message || "Scraping fehlgeschlagen" };
      emit();
    }
  })();
}

export function stop() {
  activeController?.abort();
  activeController = null;
  state = { ...state, status: "cancelled", current: "Scraping abgebrochen" };
  if (state.jobId) {
    upsertJob({
      jobId: state.jobId,
      status: "cancelled",
      companies: state.companies,
      events: state.events,
      counts: state.counts,
      current: "Abgebrochen",
      completedAt: new Date().toISOString(),
    });
  }
  emit();
}

export function reset() {
  activeController?.abort();
  activeController = null;
  state = initialState;
  emit();
}

export function isRunning() {
  return state.status === "running";
}