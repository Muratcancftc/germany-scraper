"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { getJobs, ScrapeJob } from "@/lib/api/client";

const STATUS_LABEL: Record<string, string> = {
  queued: "In Warteschlange",
  starting: "Startet",
  running: "Läuft",
  completed: "Abgeschlossen",
  failed: "Fehlgeschlagen",
  cancelled: "Abgebrochen",
};

export default function JobsPage() {
  const { data: jobs = [] as ScrapeJob[], isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: getJobs,
    refetchInterval: 5000,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Historie</h1>
      {isLoading ? (
        <p className="text-gray-500">Laden...</p>
      ) : jobs.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-gray-500 mb-4">Noch keine Scrapes vorhanden.</p>
          <Link href="/scraping" className="inline-block bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700">
            Neuen Scrape starten
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left py-3 px-4">#</th>
                <th className="text-left py-3 px-4">Datum</th>
                <th className="text-left py-3 px-4">Städte</th>
                <th className="text-left py-3 px-4">Kategorien</th>
                <th className="text-left py-3 px-4">Gefunden</th>
                <th className="text-left py-3 px-4">Gespeichert</th>
                <th className="text-left py-3 px-4">Status</th>
                <th className="text-left py-3 px-4">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id} className="border-b hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium">{job.id}</td>
                  <td className="py-3 px-4">{new Date(job.created_at).toLocaleString("de-DE")}</td>
                  <td className="py-3 px-4">{job.city_count}</td>
                  <td className="py-3 px-4">{job.category_count}</td>
                  <td className="py-3 px-4">{job.total_found}</td>
                  <td className="py-3 px-4">{job.total_added}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      job.status === "completed" ? "bg-green-100 text-green-700" :
                      job.status === "running" || job.status === "starting" ? "bg-blue-100 text-blue-700" :
                      job.status === "failed" || job.status === "cancelled" ? "bg-red-100 text-red-700" :
                      "bg-gray-100 text-gray-600"
                    }`}>
                      {STATUS_LABEL[job.status] || job.status}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <Link href={`/scraping/${job.id}`} className="text-blue-600 hover:underline text-sm">
                      Anzeigen
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
