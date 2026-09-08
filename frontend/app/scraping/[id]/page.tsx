"use client";

import Link from "next/link";

export default function JobDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
      <h1 className="text-2xl font-bold mb-3">Job #{params.id}</h1>
      <p className="text-gray-500 mb-6">
        Ergebnisse werden live angezeigt, solange der Scrape läuft. Da die
        Anwendung auf Vercel ohne Datenbank läuft, werden Ergebnisse beim
        Aktualisieren der Seite verworfen.
      </p>
      <Link
        href="/scraping"
        className="inline-block bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700"
      >
        Neuen Scrape starten
      </Link>
    </div>
  );
}