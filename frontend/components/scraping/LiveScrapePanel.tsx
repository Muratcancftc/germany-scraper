"use client";

import { useState } from "react";
import { Company, exportExcel, exportPdf } from "@/lib/api/client";
import { JobStreamState } from "@/hooks/useJobStream";

const STATUS_LABEL: Record<string, string> = {
  running: "Läuft",
  completed: "Abgeschlossen",
  failed: "Fehlgeschlagen",
  cancelled: "Abgebrochen",
};

export function StatusBadge({ status }: { status: string }) {
  const color =
    status === "completed"
      ? "bg-green-100 text-green-700"
      : status === "running"
      ? "bg-blue-100 text-blue-700"
      : status === "failed" || status === "cancelled"
      ? "bg-red-100 text-red-700"
      : "bg-gray-100 text-gray-600";
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${color}`}>
      {STATUS_LABEL[status] || status}
    </span>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

export function LiveScrapePanel({ state }: { state: JobStreamState }) {
  const [hasEmail, setHasEmail] = useState(false);
  const [hasPhone, setHasPhone] = useState(false);
  const [query, setQuery] = useState("");
  const [exporting, setExporting] = useState<null | "excel" | "pdf">(null);

  const companies = state.companies;
  let filtered = companies;
  if (hasEmail) filtered = filtered.filter((c) => c.email);
  if (hasPhone) filtered = filtered.filter((c) => c.phone);
  if (query) filtered = filtered.filter((c) => (c.name || "").toLowerCase().includes(query.toLowerCase()));

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
    <div className="mt-8">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h2 className="text-2xl font-bold">
            Scrape Job {state.jobId ? `#${state.jobId}` : ""}
          </h2>
          <p className="text-sm text-gray-500">
            {running ? "Scraping läuft..." : STATUS_LABEL[state.status] || ""}
          </p>
        </div>
        <div className="flex gap-2 items-center">
          {done && (
            <>
              <button
                onClick={() => handleExport("excel")}
                disabled={exporting !== null}
                className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                {exporting === "excel" ? "Erstellt..." : "Excel herunterladen"}
              </button>
              <button
                onClick={() => handleExport("pdf")}
                disabled={exporting !== null}
                className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                {exporting === "pdf" ? "Erstellt..." : "PDF herunterladen"}
              </button>
            </>
          )}
          <StatusBadge status={state.status} />
        </div>
      </div>

      {state.error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {state.error}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
        <StatCard label="Gefunden" value={state.counts.found} />
        <StatCard label="Neu" value={state.counts.added} />
        <StatCard label="Duplikate" value={state.counts.duplicates + state.counts.merged} />
        <StatCard label="Fehler" value={state.counts.failed} />
        <StatCard label="Gesamt" value={companies.length} />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <p className="text-sm text-gray-600 mb-2">
          {state.current || "Starte..."}
        </p>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-3 rounded-full transition-all ${running ? "bg-blue-600" : "bg-green-600"}`}
            style={{ width: `${running ? 100 : 100}%` }}
          />
        </div>
        {running && <p className="text-xs text-gray-400 mt-1">Live-Daten werden gestreamt...</p>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <h3 className="text-lg font-semibold mb-3">Live-Aktivitäten</h3>
          <div className="h-96 overflow-y-auto font-mono text-xs bg-gray-900 text-green-400 rounded-lg p-3 space-y-1">
            {state.events.length === 0 && (
              <p className="text-gray-500">Noch keine Aktivitäten...</p>
            )}
            {state.events.map((e, i) => (
              <div key={i} className="flex gap-2">
                <span className="text-gray-500 shrink-0">
                  {new Date(e.timestamp).toLocaleTimeString("de-DE")}
                </span>
                <span>{e.message || e.event_type}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold">Resultate</h3>
            <div className="flex gap-3">
              <label className="flex items-center gap-1 text-xs text-gray-600">
                <input type="checkbox" checked={hasEmail} onChange={(e) => setHasEmail(e.target.checked)} className="rounded" />
                nur mit E-Mail
              </label>
              <label className="flex items-center gap-1 text-xs text-gray-600">
                <input type="checkbox" checked={hasPhone} onChange={(e) => setHasPhone(e.target.checked)} className="rounded" />
                nur mit Telefon
              </label>
            </div>
          </div>
          <input
            type="text"
            placeholder="Suchen..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full mb-3 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
          />
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-50">
                <tr className="border-b">
                  <th className="text-left py-2 px-2">Firma</th>
                  <th className="text-left py-2 px-2">Telefon</th>
                  <th className="text-left py-2 px-2">E-Mail</th>
                  <th className="text-left py-2 px-2">Adresse</th>
                  <th className="text-left py-2 px-2">Website</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr><td colSpan={5} className="py-6 text-center text-gray-400">Noch keine Ergebnisse</td></tr>
                )}
                {filtered.map((c, i) => (
                  <tr key={i} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-2 font-medium">{c.name || "-"}</td>
                    <td className="py-2 px-2">{c.phone || <span className="text-gray-300">Nicht gefunden</span>}</td>
                    <td className="py-2 px-2">{c.email || <span className="text-gray-300">Nicht gefunden</span>}</td>
                    <td className="py-2 px-2">
                      {[c.street, c.house_number, c.postal_code, c.city].filter(Boolean).join(" ") || <span className="text-gray-300">Nicht gefunden</span>}
                    </td>
                    <td className="py-2 px-2">{c.website ? <a href={c.website} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">{c.website}</a> : <span className="text-gray-300">Nicht gefunden</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}