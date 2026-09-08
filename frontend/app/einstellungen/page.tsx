"use client";

import { useState } from "react";
import { Settings, ShieldCheck, Info } from "lucide-react";

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">Einstellungen</h1>
        <p className="mt-1 text-sm text-slate-400">Konto und System-Informationen.</p>
      </div>

      <div className="stagger grid grid-cols-1 gap-5 lg:grid-cols-2">
        <section className="card p-6">
          <div className="mb-5 flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/20 to-indigo-500/5 ring-1 ring-inset ring-indigo-400/20">
              <Settings className="h-4 w-4 text-indigo-300" />
            </div>
            <h2 className="text-base font-semibold text-white">Konto</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">Benutzername</label>
              <input type="text" className="input-field" defaultValue="admin" disabled />
              <p className="mt-1 text-xs text-slate-500">Wird über die Umgebungsvariable ADMIN_USERNAME verwaltet.</p>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">Passwort</label>
              <input type="password" className="input-field" placeholder="••••••••" disabled />
              <p className="mt-1 text-xs text-slate-500">Wird über die Umgebungsvariable ADMIN_PASSWORD verwaltet.</p>
            </div>
            {saved && (
              <p className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2.5 text-sm text-emerald-300">
                Einstellungen gespeichert.
              </p>
            )}
            <button onClick={() => setSaved(true)} className="btn-primary">Speichern</button>
          </div>
        </section>

        <section className="card p-6">
          <div className="mb-5 flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 ring-1 ring-inset ring-emerald-400/20">
              <ShieldCheck className="h-4 w-4 text-emerald-300" />
            </div>
            <h2 className="text-base font-semibold text-white">Architektur</h2>
          </div>
          <div className="space-y-3 text-sm">
            {[
              ["Backend", "Vercel Function · FastAPI"],
              ["Scraping", "HTTP-first · Camoufox-Fallback"],
              ["Realtime", "SSE Streaming"],
              ["Storage", "In-Memory (keine DB)"],
              ["AI / LLM", "Nicht verwendet"],
            ].map(([k, v]) => (
              <div key={k} className="flex items-center justify-between rounded-xl bg-white/[0.03] px-4 py-3 ring-1 ring-inset ring-white/[0.06]">
                <span className="text-slate-400">{k}</span>
                <span className="font-medium text-slate-200">{v}</span>
              </div>
            ))}
            <div className="mt-4 flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 text-xs text-slate-400">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
              <p>
                Diese App läuft vollständig auf Vercel Pro mit Fluid Compute.
                Job-Ergebnisse bleiben nur während der aktiven Session erhalten.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}