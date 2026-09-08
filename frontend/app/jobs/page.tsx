"use client";

import Link from "next/link";
import { Building2, ArrowRight } from "lucide-react";

export default function JobsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">Ergebnisse</h1>
        <p className="mt-1 text-sm text-slate-400">
          Alle Scraping-Ergebnisse werden live angezeigt und direkt exportiert.
        </p>
      </div>

      <div className="card overflow-hidden">
        <div className="flex flex-col items-center gap-4 px-6 py-14 text-center">
          <div className="relative">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 blur-md opacity-50" />
            <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
              <Building2 className="h-7 w-7 text-white" />
            </div>
          </div>
          <div className="max-w-md">
            <h2 className="text-lg font-semibold text-white">Noch keine gespeicherten Ergebnisse</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">
              Ergebnisse werden während des Scrapings live gestreamt und können
              dort direkt als <span className="font-medium text-emerald-400">Excel</span> oder{" "}
              <span className="font-medium text-red-400">PDF</span> exportiert werden.
            </p>
            <p className="mt-3 text-xs text-slate-500">
              Hinweis: Da die App ohne Datenbank auf Vercel läuft, wird keine
              Historie gespeichert — nach dem Schließen der Seite sind die
              Ergebnisse verworfen.
            </p>
          </div>
          <Link href="/scraping" className="btn-primary mt-2">
            Neuen Scrape starten
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}