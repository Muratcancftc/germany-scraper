"use client";

import { Company, ScrapeEvent } from "@/lib/api/client";

export interface SavedJob {
  jobId: number;
  status: "running" | "completed" | "failed" | "cancelled";
  companies: Partial<Company>[];
  events: ScrapeEvent[];
  counts: {
    found: number;
    added: number;
    duplicates: number;
    merged: number;
    failed: number;
  };
  current: string;
  startedAt: string;
  completedAt?: string;
}

const STORAGE_KEY = "germany-scraper-jobs";

let jobs: SavedJob[] = load();
const listeners = new Set<() => void>();

function load(): SavedJob[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SavedJob[]) : [];
  } catch {
    return [];
  }
}

function persist() {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(jobs.slice(0, 20)));
  } catch {
    // ignore
  }
}

function emit() {
  listeners.forEach((l) => l());
}

export function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function getJobs(): SavedJob[] {
  return jobs;
}

export function upsertJob(update: Partial<SavedJob> & { jobId: number }) {
  const existing = jobs.find((j) => j.jobId === update.jobId);
  if (existing) {
    existing.companies = update.companies ?? existing.companies;
    existing.events = update.events ?? existing.events;
    existing.counts = update.counts ?? existing.counts;
    existing.status = update.status ?? existing.status;
    existing.current = update.current ?? existing.current;
    existing.completedAt = update.completedAt ?? existing.completedAt;
  } else {
    jobs = [
      {
        jobId: update.jobId,
        status: update.status ?? "running",
        companies: update.companies ?? [],
        events: update.events ?? [],
        counts: update.counts ?? { found: 0, added: 0, duplicates: 0, merged: 0, failed: 0 },
        current: update.current ?? "",
        startedAt: new Date().toISOString(),
        completedAt: update.completedAt,
      },
      ...jobs,
    ];
  }
  persist();
  emit();
}

export function clearJobs() {
  jobs = [];
  persist();
  emit();
}