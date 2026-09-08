"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  cancelJob,
  exportExcel,
  exportPdf,
  getJob,
  getJobCompanies,
  getJobEvents,
  Company,
  ScrapeEvent,
} from "@/lib/api/client";
import { useJobSocket } from "@/hooks/useJobSocket";

const STATUS_LABEL: Record<string, string> = {
  queued: "In Warteschlange",
  starting: "Startet",
  running: "Läuft",
  completed: "Abgeschlossen",
  failed: "Fehlgeschlagen",
  cancelled: "Abgebrochen",
};

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "completed"
      ? "bg-green-100 text-green-700"
      : status === "running" || status === "starting"
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

export default function JobDetailPage({ params }: { params: { id: string } }) {
  const jobId = Number(params.id);
  const router = useRouter();
  const { events: liveEvents, companies: liveCompanies, connected } = useJobSocket(jobId);

  const [job, setJob] = useState<any>(null);
  const [dbEvents, setDbEvents] = useState<ScrapeEvent[]>([]);
  const [dbCompanies, setDbCompanies] = useState<Company[]>([]);
  const [hasEmail, setHasEmail] = useState(false);
  const [hasPhone, setHasPhone] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [j, ev, comp] = await Promise.all([
          getJob(jobId),
          getJobEvents(jobId),
          getJobCompanies(jobId),
        ]);
        setJob(j);
        setDbEvents(ev);
        setDbCompanies(comp);
      } catch {
        router.push("/jobs");
      }
    })();
  }, [jobId, router]);

  const allCompanies = useMemo(() => {
    const live = liveCompanies as Partial<Company>[];
    const byKey = new Map<string, Company | Partial<Company>>();
    for (const c of dbCompanies) byKey.set(c.name, c);
    for (const c of live) if (c.name && !byKey.has(c.name)) byKey.set(c.name, c);
    let list = Array.from(byKey.values());
    if (hasEmail) list = list.filter((c) => c.email);
    if (hasPhone) list = list.filter((c) => c.phone);
    if (query) list = list.filter((c) => (c.name || "").toLowerCase().includes(query.toLowerCase()));
    return list;
  }, [dbCompanies, liveCompanies, hasEmail, hasPhone, query]);

  const allEvents = useMemo(() => [...dbEvents, ...liveEvents].sort((a, b) => a.id - b.id), [dbEvents, liveEvents]);

  const progress = job && job.total_found > 0
    ? Math.round(((job.total_added + job.total_duplicates + job.total_merged) / job.total_found) * 100)
    : 0;

  const handleExport = async (type: "excel" | "pdf") => {
    try {
      const res = type === "excel" ? await exportExcel(jobId) : await exportPdf(jobId);
      if (res.file_url) window.location.href = res.file_url;
    } catch (e) {
      alert("Export fehlgeschlagen");
    }
  };

  const handleCancel = async () => {
    await cancelJob(jobId);
    setJob((prev: any) => ({ ...prev, status: "cancelled" }));
  };

  if (!job) return <p className="p-8 text-gray-500">Laden...</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold">Scrape Job #{job.id}</h1>
          <p className="text-sm text-gray-500">
            Erstellt am {new Date(job.created_at).toLocaleString("de-DE")}
            {connected ? " • Live verbunden" : ""}
          </p>
        </div>
        <div className="flex gap-2">
          {(job.status === "completed" || job.status === "running") && (
            <>
              <button
                onClick={() => handleExport("excel")}
                className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-50"
              >
                Excel herunterladen
              </button>
              <button
                onClick={() => handleExport("pdf")}
                className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-50"
              >
                PDF herunterladen
              </button>
            </>
          )}
          {(job.status === "running" || job.status === "queued" || job.status === "starting") && (
            <button
              onClick={handleCancel}
              className="bg-red-50 border border-red-200 text-red-600 px-4 py-2 rounded-lg font-medium hover:bg-red-100"
            >
              Abbrechen
            </button>
          )}
          <StatusBadge status={job.status} />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <StatCard label="Gefunden" value={job.total_found} />
        <StatCard label="Gespeichert" value={job.total_added} />
        <StatCard label="Duplikate" value={job.total_duplicates + job.total_merged} />
        <StatCard label="Fehler" value={job.total_failed} />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div className="bg-blue-600 h-3 rounded-full transition-all" style={{ width: `${Math.min(progress, 100)}%` }} />
        </div>
        <div className="flex justify-between mt-1 text-sm text-gray-500">
          <span>Fortschritt</span>
          <span>{Math.min(progress, 100)}%</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <h2 className="text-lg font-semibold mb-3">Live-Aktivitäten</h2>
          <div className="h-96 overflow-y-auto font-mono text-xs bg-gray-900 text-green-400 rounded-lg p-3 space-y-1">
            {allEvents.length === 0 && (
              <p className="text-gray-500">Noch keine Aktivitäten...</p>
            )}
            {allEvents.map((e, i) => (
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
            <h2 className="text-lg font-semibold">Resultate</h2>
            <div className="flex gap-2">
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
                {allCompanies.length === 0 && (
                  <tr><td colSpan={5} className="py-6 text-center text-gray-400">Noch keine Ergebnisse</td></tr>
                )}
                {allCompanies.map((c, i) => (
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

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
