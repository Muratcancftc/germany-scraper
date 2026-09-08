"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Company, ScrapeEvent, wsUrl } from "@/lib/api/client";

interface LiveEvent extends ScrapeEvent {
  payload?: { company?: Partial<Company> };
}

function companyKey(c: Partial<Company>): string {
  if (c.website) return `w:${c.website}`;
  if (c.phone) return `p:${c.phone}`;
  if (c.email) return `e:${c.email}`;
  return `n:${c.name ?? ""}`;
}

export function useJobSocket(jobId: number | null) {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [companies, setCompanies] = useState<Partial<Company>[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const reset = useCallback(() => {
    setEvents([]);
    setCompanies([]);
  }, []);

  useEffect(() => {
    if (jobId == null) return;
    reset();

    const ws = new WebSocket(wsUrl(jobId));
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (msg) => {
      try {
        const data: LiveEvent = JSON.parse(msg.data);
        setEvents((prev) => [...prev, data]);

        const company = data.payload?.company;
        if (company) {
          if (data.event_type === "company_added") {
            setCompanies((prev) => [company, ...prev]);
          } else if (data.event_type === "company_merged") {
            const key = companyKey(company);
            setCompanies((prev) => {
              const idx = prev.findIndex((c) => companyKey(c) === key);
              if (idx === -1) return [company, ...prev];
              const next = [...prev];
              next[idx] = { ...next[idx], ...company };
              return next;
            });
          }
        }
      } catch {
        // ignore malformed frames
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [jobId, reset]);

  return { events, companies, connected };
}