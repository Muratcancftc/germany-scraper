"use client";

import { useSyncExternalStore } from "react";
import Link from "next/link";
import { History, Building2, ArrowRight, Loader2, CheckCircle2, XCircle, Ban } from "lucide-react";
import { getJobs, subscribe } from "@/lib/jobStore";

function statusBadge(status: string) {
  const cls =
    status === "completed"
      ? "bg-emerald-500/15 text-emerald-300 ring-emerald-400/20"
      : status === "running"
      ? "bg-blue-500/15 text-blue-300 ring-blue-400/20"
      : status === "cancelled"
      ? "bg-amber-500/15 text-amber-300 ring-amber-400/20"
      : "bg-red-500/15 text-red-300 ring-red-400/20";
  const label =
    status === "completed"
      ? "Abgeschlossen"
      : status === "running"
      ? "Läuft"
      : status === "cancelled"
      ? "Abgebrochen"
      : "Fehlgeschlagen";
  const Icon =
    status === "completed"
      ? CheckCircle2
      : status === "running"
      ? Loader2
      : status === "cancelled"
      ? Ban
      : XCircle;
  return (
    <span className={`badge ring-1 ring-inset ${cls}`}>
      <Icon className={status === "running" ? "h-3 w-3 animate-spin" : "h-3 w-3"} />
      {label}
    </span>
  );
}

export default function HistoryPage() {
  const jobs = useSyncExternalStore(subscribe, getJobs);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">Historie</h1>
        <p className="mt-1 text-sm text-slate-400">
          Alle Scraping-Jobs dieser Session — laufende werden live aktualisiert.
        </p>
      </div>

      {jobs.length === 0 ? (
        <div className="card overflow-hidden">
          <div className="flex flex-col items-center gap-4 px-6 py-14 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.04] ring-1 ring-inset ring-white/10">
              <History className="h-7 w-7 text-slate-400" />
            </div>
            <div className="max-w-md">
              <h2 className="text-lg font-semibold text-white">Noch keine Historie</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">
                Starten Sie einen Scrape — der Job erscheint hier sofort,
                während er läuft, und bleibt bis zum Schließen des Tabs
                verfügbar.
              </p>
            </div>
            <Link href="/scraping" className="btn-primary mt-2">
              Neuen Scrape starten
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      ) : (
        <div className="stagger grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {jobs.map((job) => (
            <Link
              key={job.jobId}
              href="/jobs"
              className="card group relative overflow-hidden p-5 transition-all duration-200 hover:-translate-y-0.5 hover:border-white/[0.14]"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/20 to-indigo-500/5 ring-1 ring-inset ring-indigo-400/20">
                    <Building2 className="h-5 w-5 text-indigo-300" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-white">Job #{job.jobId}</h2>
                    <p className="text-xs text-slate-500">
                      {new Date(job.startedAt).toLocaleString("de-DE")}
                    </p>
                  </div>
                </div>
                {statusBadge(job.status)}
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2">
                {[
                  ["Gefunden", job.counts.found],
                  ["Firmen", job.companies.length],
                  ["Fehler", job.counts.failed],
                ].map(([label, val]) => (
                  <div key={String(label)} className="rounded-xl bg-white/[0.03] px-3 py-2 text-center ring-1 ring-inset ring-white/[0.06]">
                    <p className="text-lg font-bold text-white">{val}</p>
                    <p className="text-[11px] text-slate-500">{label}</p>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center justify-between">
                <p className="truncate text-xs text-slate-500">{job.current || "..."}</p>
                <span className="text-xs font-medium text-indigo-400 opacity-0 transition-opacity group-hover:opacity-100">
                  Ergebnisse ansehen →
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}