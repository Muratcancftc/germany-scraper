"use client";

import { useSyncExternalStore } from "react";
import {
  subscribe,
  getSnapshot,
  start,
  stop,
  reset,
  JobStreamState,
} from "@/lib/scrapeStore";

export type { JobStreamState };

/**
 * React hook over the global scrape store.
 * The stream lives at module scope, so leaving the scraping page does not
 * cancel it — returning to the page shows the live panel again.
 */
export function useJobStream() {
  const state: JobStreamState = useSyncExternalStore(subscribe, getSnapshot);
  return { state, start, stop, reset };
}