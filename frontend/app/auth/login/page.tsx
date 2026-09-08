"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api/client";
import { Radar, ShieldCheck, Zap, ArrowRight, Lock, User } from "lucide-react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(username, password);
      localStorage.setItem("token", data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen overflow-hidden">
      {/* Ambient glows */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-40 -top-40 h-[500px] w-[500px] rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="absolute -bottom-40 -right-40 h-[500px] w-[500px] rounded-full bg-purple-600/20 blur-[120px]" />
        <div className="absolute left-1/2 top-1/3 h-[300px] w-[300px] -translate-x-1/2 rounded-full bg-violet-500/10 blur-[100px]" />
      </div>

      <div className="relative mx-auto flex w-full max-w-md flex-col items-center justify-center px-6 py-12">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center">
          <div className="relative mb-4">
            <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-600 blur-xl opacity-60" />
            <div className="relative flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-2xl">
              <Radar className="h-8 w-8 text-white" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white">
            Germany <span className="text-gradient">Scraper</span>
          </h1>
          <p className="mt-1 text-sm text-slate-500">Pro Panel — Unternehmens-Scraping</p>
        </div>

        {/* Card */}
        <div className="card w-full p-8">
          <h2 className="text-xl font-bold text-white">Anmelden</h2>
          <p className="mt-1 text-sm text-slate-500">Geben Sie Ihre Zugangsdaten ein</p>

          {error && (
            <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-5">
            <div>
              <label className="mb-1.5 flex items-center gap-1.5 text-sm font-medium text-slate-300">
                <User className="h-3.5 w-3.5 text-slate-500" />
                Benutzername
              </label>
              <input
                type="text"
                className="input-field"
                placeholder="admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </div>
            <div>
              <label className="mb-1.5 flex items-center gap-1.5 text-sm font-medium text-slate-300">
                <Lock className="h-3.5 w-3.5 text-slate-500" />
                Passwort
              </label>
              <input
                type="password"
                className="input-field"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-3">
              {loading ? "Anmeldung..." : "Anmelden"}
              {!loading && <ArrowRight className="h-4 w-4" />}
            </button>
          </form>
        </div>

        {/* Feature badges */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-slate-500">
          <span className="flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5 text-amber-400" /> Echtzeit · SSE
          </span>
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" /> Kein AI · Kein DB
          </span>
          <span className="flex items-center gap-1.5">
            <Radar className="h-3.5 w-3.5 text-indigo-400" /> Camoufox
          </span>
        </div>
      </div>
    </div>
  );
}