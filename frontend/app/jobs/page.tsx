"use client";

import Link from "next/link";

export default function JobsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Ergebnisse</h1>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500 mb-4">
          Scraping-Ergebnisse werden live auf der Scraping-Seite angezeigt und
          können dort direkt als Excel oder PDF exportiert werden.
        </p>
        <p className="text-gray-400 mb-6 text-sm">
          Da diese App ohne Datenbank auf Vercel läuft, wird keine Historie
          gespeichert — nach dem Schließen der Seite sind die Ergebnisse weg.
        </p>
        <Link
          href="/scraping"
          className="inline-block bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700"
        >
          Neuen Scrape starten
        </Link>
      </div>
    </div>
  );
}