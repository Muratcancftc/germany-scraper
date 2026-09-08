"use client";

import { useState } from "react";
import { Company, exportExcel, exportPdf } from "@/lib/api/client";
import { JobStreamState } from "@/hooks/useJobStream";
import {
  FileSpreadsheet,
  FileText,
  Search,
  Building2,
  Sparkles,
  Copy,
  AlertTriangle,
  Loader2,
  CheckCircle2,
  List,
  Mail,
  Phone,
  Globe,
  Square,
} from "lucide-react";

const STATUS_LABEL: Record<string, string> = {
  running: "Läuft",
  completed: "Abgeschlossen",
  failed: "Fehlgeschlagen",
  cancelled: "Abgebrochen",
};

function StatCard({ label, value, icon, gradient, glow }: { label: string; value: number; icon: React.ReactNode; gradient: string; glow: string }) {
  return (
    <div className="card relative overflow-hidden p-4">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} shadow-lg ${glow}`}>
          {icon}
        </div>
        <div>
          <p className="text-xs font-medium text-slate-400">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
      </div>
    </div>
  );
}

export function LiveScrapePanel({
  state,
  onStop,
}: {
  state: JobStreamState;
  onStop?: () => void;
}) {
  const [hasEmail, setHasEmail] = useState(false);
  const [hasPhone, setHasPhone] = useState(false);
  const [query, setQuery] = useState("");
  const [exporting, setExporting] = useState<null | "excel" | "pdf">(null);

  const companies = state.companies;
  let filtered = companies;
  if (hasEmail) filtered = filtered.filter((c) => c.email);
  if (hasPhone) filtered = filtered.filter((c) => c.phone);
  if (query)
    filtered = filtered.filter((c) =>
      (c.name || "").toLowerCase().includes(query.toLowerCase())
    );

  const running = state.status === "running";
  const done = state.status === "completed";

  const handleExport = async (type: "excel" | "pdf") => {
    setExporting(type);
    try {
      if (type === "excel") await exportExcel(companies);
      else await exportPdf(companies);
    } catch {
      alert("Export fehlgeschlagen");
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 blur-md opacity-50" />
            <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
              <Building2 className="h-5 w-5 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-xl font-bold text-white sm:text-2xl">
              Scrape Job {state.jobId ? `#${state.jobId}` : ""}
            </h1>
            <p className="text-sm text-slate-400">
              {running ? "Scraping läuft..." : STATUS_LABEL[state.status] || ""}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {running && onStop && (
            <button onClick={onStop} className="btn-danger">
              <Square className="h-3.5 w-3.5" />
              Stoppen
            </button>
          )}
          {(done || running) && companies.length > 0 && (
            <>
              <button onClick={() => handleExport("excel")} disabled={exporting !== null} className="btn-secondary">
                <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
                {exporting === "excel" ? "Erstellt..." : "Excel"}
              </button>
              <button onClick={() => handleExport("pdf")} disabled={exporting !== null} className="btn-secondary">
                <FileText className="h-4 w-4 text-red-400" />
                {exporting === "pdf" ? "Erstellt..." : "PDF"}
              </button>
            </>
          )}
          <span
            className={`badge ${
              state.status === "completed"
                ? "bg-emerald-500/15 text-emerald-300 ring-1 ring-inset ring-emerald-400/20"
                : state.status === "running"
                ? "bg-blue-500/15 text-blue-300 ring-1 ring-inset ring-blue-400/20"
                : state.status === "failed" || state.status === "cancelled"
                ? "bg-red-500/15 text-red-300 ring-1 ring-inset ring-red-400/20"
                : "bg-white/[0.06] text-slate-300 ring-1 ring-inset ring-white/10"
            }`}
          >
            {running && <span className="live-dot h-1.5 w-1.5 rounded-full bg-blue-400" />}
            {STATUS_LABEL[state.status] || state.status}
          </span>
        </div>
      </div>

      {state.error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {state.error}
        </div>
      )}

      {/* Stats */}
      <div className="stagger grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
        <StatCard label="Gefunden" value={state.counts.found} icon={<List className="h-4 w-4 text-blue-300" />} gradient="from-blue-500/20 to-blue-500/5" glow="shadow-blue-500/20" />
        <StatCard label="Neu" value={state.counts.added} icon={<Sparkles className="h-4 w-4 text-indigo-300" />} gradient="from-indigo-500/20 to-indigo-500/5" glow="shadow-indigo-500/20" />
        <StatCard label="Duplikate" value={state.counts.duplicates + state.counts.merged} icon={<Copy className="h-4 w-4 text-amber-300" />} gradient="from-amber-500/20 to-amber-500/5" glow="shadow-amber-500/20" />
        <StatCard label="Fehler" value={state.counts.failed} icon={<AlertTriangle className="h-4 w-4 text-red-300" />} gradient="from-red-500/20 to-red-500/5" glow="shadow-red-500/20" />
        <StatCard label="Gesamt" value={companies.length} icon={<Building2 className="h-4 w-4 text-emerald-300" />} gradient="from-emerald-500/20 to-emerald-500/5" glow="shadow-emerald-500/20" />
      </div>

      {/* Progress */}
      <div className="card p-5">
        <div className="mb-2 flex items-center justify-between">
          <p className="flex items-center gap-2 text-sm font-medium text-slate-300">
            {running ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
                {state.current || "Starte..."}
              </>
            ) : (
              <>
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                {state.current || STATUS_LABEL[state.status] || "Fertig"}
              </>
            )}
          </p>
          {running && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
              <span className="live-dot h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Live-Stream
            </span>
          )}
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/[0.06]">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              running
                ? "bg-gradient-to-r from-indigo-500 via-violet-500 to-purple-500"
                : "bg-gradient-to-r from-emerald-500 to-emerald-400"
            }`}
            style={{ width: "100%" }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        {/* Live log */}
        <section className="card flex flex-col">
          <div className="flex items-center gap-2 border-b border-white/[0.06] px-5 py-4">
            <span className="live-dot h-2 w-2 rounded-full bg-emerald-400" />
            <h3 className="text-base font-semibold text-white">Live-Aktivitäten</h3>
          </div>
          <div className="max-h-[28rem] flex-1 space-y-1 overflow-y-auto p-4 font-mono text-xs">
            {state.events.length === 0 && (
              <p className="py-8 text-center text-slate-500">Noch keine Aktivitäten...</p>
            )}
            {state.events.map((e, i) => (
              <div key={i} className="flex gap-2 rounded-lg px-2 py-1.5 hover:bg-white/[0.04]">
                <span className="shrink-0 text-slate-500">
                  {new Date(e.timestamp).toLocaleTimeString("de-DE")}
                </span>
                <span className="text-slate-300">{e.message || e.event_type}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Results */}
        <section className="card flex flex-col">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-4">
            <h3 className="flex items-center gap-2 text-base font-semibold text-white">
              <Building2 className="h-4 w-4 text-indigo-400" />
              Resultate
              <span className="badge bg-indigo-500/15 text-indigo-300 ring-1 ring-inset ring-indigo-400/20">
                {companies.length}
              </span>
            </h3>
            <div className="flex items-center gap-4">
              <label className="flex cursor-pointer items-center gap-1.5 text-xs text-slate-400">
                <input type="checkbox" checked={hasEmail} onChange={(e) => setHasEmail(e.target.checked)} className="h-3.5 w-3.5 rounded border-slate-600 bg-transparent text-indigo-500 focus:ring-indigo-500/50" />
                nur mit E-Mail
              </label>
              <label className="flex cursor-pointer items-center gap-1.5 text-xs text-slate-400">
                <input type="checkbox" checked={hasPhone} onChange={(e) => setHasPhone(e.target.checked)} className="h-3.5 w-3.5 rounded border-slate-600 bg-transparent text-indigo-500 focus:ring-indigo-500/50" />
                nur mit Telefon
              </label>
            </div>
          </div>

          <div className="border-b border-white/[0.06] p-4">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Unternehmen suchen..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="input-field py-2 pl-10"
              />
            </div>
          </div>

          <div className="flex-1 overflow-auto">
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
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-10 text-center text-slate-500">
                      Noch keine Ergebnisse
                    </td>
                  </tr>
                )}
                {filtered.map((c, i) => (
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
      </div>
    </div>
  );
}