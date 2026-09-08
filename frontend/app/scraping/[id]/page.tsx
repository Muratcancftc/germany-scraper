"use client";

import Link from "next/link";
import { Radar, ArrowRight } from "lucide-react";

export default function JobDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">Job #{params.id}</h1>
        <p className="mt-1 text-sm text-slate-400">
          Ergebnisse werden live angezeigt, solange der Scrape läuft.
        </p>
      </div>

      <div className="card overflow-hidden">
        <div className="flex flex-col items-center gap-4 px-6 py-14 text-center">
          <div className="relative">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 blur-md opacity-50" />
            <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
              <Radar className="h-7 w-7 text-white" />
            </div>
          </div>
          <div className="max-w-md">
            <h2 className="text-lg font-semibold text-white">Job nicht mehr verfügbar</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">
              Da diese App ohne Datenbank läuft, werden Ergebnisse beim
              Aktualisieren der Seite verworfen. Starten Sie einfach einen
              neuen Scrape.
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