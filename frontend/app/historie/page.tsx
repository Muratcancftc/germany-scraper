"use client";

import Link from "next/link";
import { History, ArrowRight } from "lucide-react";

export default function HistoryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">Historie</h1>
        <p className="mt-1 text-sm text-slate-400">
          Frühere Scraping-Jobs werden nicht persistiert.
        </p>
      </div>

      <div className="card overflow-hidden">
        <div className="flex flex-col items-center gap-4 px-6 py-14 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.04] ring-1 ring-inset ring-white/10">
            <History className="h-7 w-7 text-slate-400" />
          </div>
          <div className="max-w-md">
            <h2 className="text-lg font-semibold text-white">Noch keine Historie</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">
              Diese Version arbeitet vollständig in-memory ohne Datenbank.
              Jobs werden live gestreamt und sind nur während der aktiven
              Session verfügbar.
            </p>
          </div>
          <Link href="/dashboard" className="btn-secondary mt-2">
            Zum Dashboard
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}