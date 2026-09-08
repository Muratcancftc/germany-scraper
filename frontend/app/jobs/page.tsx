"use client";

import { useSyncExternalStore, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Building2, ArrowRight, FileSpreadsheet, FileText, Search, Mail, Phone, Globe, Loader2, Database } from "lucide-react";
import { getJobs, subscribe, SavedJob } from "@/lib/jobStore";
import { exportExcel, exportPdf, getPersistedCompanies } from "@/lib/api/client";

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
    status === "completed" ? "Abgeschlossen" : status === "running" ? "Läuft" : status === "cancelled" ? "Abgebrochen" : "Fehlgeschlagen";
  return (
    <span className={`badge ring-1 ring-inset ${cls}`}>
      {status === "running" && <Loader2 className="h-3 w-3 animate-spin" />}
      {label}
    </span>
  );
}

export default function JobsPage() {
  const jobs = useSyncExternalStore(subscribe, getJobs);
  const [query, setQuery] = useState("");
  const [exporting, setExporting] = useState<null | { type: "excel" | "pdf"; jobId: number }>(null);

  const { data: persisted = [] as any[], isLoading: persistedLoading } = useQuery({
    queryKey: ["persisted-companies"],
    queryFn: getPersistedCompanies,
    retry: 1,
  });

  const filtered = query
    ? jobs.filter((j) =>
        j.companies.some((c) => (c.name || "").toLowerCase().includes(query.toLowerCase()))
      )
    : jobs;

  const handleExport = async (job: SavedJob, type: "excel" | "pdf") => {
    setExporting({ type, jobId: job.jobId });
    try {
      if (type === "excel") await exportExcel(job.companies);
      else await exportPdf(job.companies);
    } catch {
      alert("Export fehlgeschlagen");
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white sm:text-3xl">Ergebnisse</h1>
          <p className="mt-1 text-sm text-slate-400">
            Ergebnisse aus dieser Session — live gestreamt, hier gespeichert.
          </p>
        </div>
        <Link href="/scraping" className="btn-primary">
          Neuen Scrape starten
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      {jobs.length === 0 && persisted.length === 0 ? (
        <div className="card overflow-hidden">
          <div className="flex flex-col items-center gap-4 px-6 py-14 text-center">
            <div className="relative">
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 blur-md opacity-50" />
              <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
                <Building2 className="h-7 w-7 text-white" />
              </div>
            </div>
            <div className="max-w-md">
              <h2 className="text-lg font-semibold text-white">Noch keine Ergebnisse</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">
                Starten Sie einen Scrape — Ergebnisse werden live gestreamt und
                erscheinen hier automatisch.
              </p>
              <p className="mt-3 text-xs text-slate-500">
                Hinweis: Ohne Datenbank bleiben Ergebnisse nur in dieser Session
                erhalten (beim Schließen des Tabs verworfen).
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {persisted.length > 0 && (
            <section className="card overflow-hidden">
              <div className="flex items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 ring-1 ring-inset ring-emerald-400/20">
                    <Database className="h-4 w-4 text-emerald-300" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-white">Gespeicherte Firmen (Supabase)</h2>
                    <p className="text-xs text-slate-500">
                      Kalıcı olarak kayıtlı, tüm job'ların sonuçları · {persisted.length} Firmen
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={async () => {
                      try {
                        await exportExcel(persisted as any);
                      } catch {
                        alert("Export fehlgeschlagen");
                      }
                    }}
                    className="btn-secondary py-1.5"
                  >
                    <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
                    Excel
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        await exportPdf(persisted as any);
                      } catch {
                        alert("Export fehlgeschlagen");
                      }
                    }}
                    className="btn-secondary py-1.5"
                  >
                    <FileText className="h-4 w-4 text-red-400" />
                    PDF
                  </button>
                </div>
              </div>
              <div className="max-h-80 overflow-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-[#0d0d14] text-left">
                    <tr className="text-xs uppercase tracking-wide text-slate-500">
                      <th className="px-5 py-3 font-semibold">Firma</th>
                      <th className="px-3 py-3 font-semibold">Telefon</th>
                      <th className="px-3 py-3 font-semibold">E-Mail</th>
                      <th className="px-3 py-3 font-semibold">Adresse</th>
                      <th className="px-5 py-3 font-semibold">Website</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.05]">
                    {persisted.map((c, i) => (
                      <tr key={i} className="transition-colors hover:bg-emerald-500/[0.04]">
                        <td className="px-5 py-3 font-medium text-white">{c.name || "-"}</td>
                        <td className="px-3 py-3 text-slate-300">
                          {c.phone ? (
                            <span className="flex items-center gap-1.5">
                              <Phone className="h-3 w-3 text-slate-500" />
                              {c.phone}
                            </span>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-slate-300">
                          {c.email ? (
                            <a href={`mailto:${c.email}`} className="text-indigo-300 hover:underline">
                              {c.email}
                            </a>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-slate-300">
                          {[c.street, c.house_number, c.postal_code, c.city].filter(Boolean).join(" ") || <span className="text-slate-600">—</span>}
                        </td>
                        <td className="px-5 py-3">
                          {c.website ? (
                            <a href={c.website} target="_blank" rel="noreferrer" className="text-indigo-300 hover:underline">
                              {c.website.replace(/^https?:\/\//, "")}
                            </a>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
          {filtered.map((job) => (
            <section key={job.jobId} className="card overflow-hidden">
              {/* Job header */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/20 to-indigo-500/5 ring-1 ring-inset ring-indigo-400/20">
                    <Building2 className="h-4 w-4 text-indigo-300" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-white">Job #{job.jobId}</h2>
                    <p className="text-xs text-slate-500">
                      {new Date(job.startedAt).toLocaleString("de-DE")} ·{" "}
                      {job.companies.length} Firmen
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleExport(job, "excel")}
                    disabled={exporting?.jobId === job.jobId}
                    className="btn-secondary py-1.5"
                  >
                    <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
                    Excel
                  </button>
                  <button
                    onClick={() => handleExport(job, "pdf")}
                    disabled={exporting?.jobId === job.jobId}
                    className="btn-secondary py-1.5"
                  >
                    <FileText className="h-4 w-4 text-red-400" />
                    PDF
                  </button>
                  {statusBadge(job.status)}
                </div>
              </div>

              {/* Search */}
              <div className="border-b border-white/[0.06] p-4">
                <div className="relative max-w-md">
                  <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    placeholder="In diesen Ergebnissen suchen..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="input-field py-2 pl-10"
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3 px-5 py-4 sm:grid-cols-5">
                {[
                  ["Gefunden", job.counts.found],
                  ["Neu", job.counts.added],
                  ["Duplikate", job.counts.duplicates + job.counts.merged],
                  ["Fehler", job.counts.failed],
                  ["Gesamt", job.companies.length],
                ].map(([label, val]) => (
                  <div key={String(label)} className="rounded-xl bg-white/[0.03] px-4 py-3 ring-1 ring-inset ring-white/[0.06]">
                    <p className="text-xs text-slate-400">{label}</p>
                    <p className="text-xl font-bold text-white">{val}</p>
                  </div>
                ))}
              </div>

              {/* Companies table */}
              <div className="max-h-[30rem] overflow-auto border-t border-white/[0.06]">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-[#0d0d14] text-left">
                    <tr className="text-xs uppercase tracking-wide text-slate-500">
                      <th className="px-5 py-3 font-semibold">Firma</th>
                      <th className="px-3 py-3 font-semibold">Telefon</th>
                      <th className="px-3 py-3 font-semibold">E-Mail</th>
                      <th className="px-3 py-3 font-semibold">Adresse</th>
                      <th className="px-5 py-3 font-semibold">Website</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.05]">
                    {job.companies.length === 0 && (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-slate-500">
                          Keine Firmen gefunden
                        </td>
                      </tr>
                    )}
                    {job.companies.map((c, i) => (
                      <tr key={i} className="transition-colors hover:bg-indigo-500/[0.04]">
                        <td className="px-5 py-3 font-medium text-white">{c.name || "-"}</td>
                        <td className="px-3 py-3 text-slate-300">
                          {c.phone ? (
                            <span className="flex items-center gap-1.5">
                              <Phone className="h-3 w-3 text-slate-500" />
                              {c.phone}
                            </span>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-slate-300">
                          {c.email ? (
                            <a href={`mailto:${c.email}`} className="flex items-center gap-1.5 text-indigo-300 hover:underline">
                              <Mail className="h-3 w-3 text-slate-500" />
                              {c.email}
                            </a>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-slate-300">
                          {[c.street, c.house_number, c.postal_code, c.city].filter(Boolean).join(" ") || <span className="text-slate-600">—</span>}
                        </td>
                        <td className="px-5 py-3">
                          {c.website ? (
                            <a href={c.website} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 text-indigo-300 hover:underline">
                              <Globe className="h-3 w-3 text-slate-500" />
                              {c.website.replace(/^https?:\/\//, "")}
                            </a>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}