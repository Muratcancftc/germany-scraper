"use client";

import { useCallback, useRef, useState } from "react";
import { Company, ScrapeEvent, streamJob } from "@/lib/api/client";

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

export function useJobStream() {
  const [state, setState] = useState<JobStreamState>(initialState);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState(initialState);
  }, []);

  const start = useCallback(
    async (config: { city_ids: number[]; category_ids: number[]; max_results?: number }) => {
      abortRef.current?.abort();
      setState(initialState);
      setState((s) => ({ ...s, status: "running" }));

      try {
        for await (const event of streamJob(config)) {
          setState((prev) => {
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
            return next;
          });
        }
      } catch (e: any) {
        setState((s) => ({
          ...s,
          status: "failed",
          error: e.message || "Scraping fehlgeschlagen",
        }));
      }
    },
    []
  );

  return { state, start, reset };
}