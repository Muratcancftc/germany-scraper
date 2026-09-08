"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { getDashboardStats, DashboardStats } from "@/lib/api/client";
import {
  Building2,
  TrendingUp,
  Activity,
  CheckCircle2,
  Radar,
  ArrowRight,
} from "lucide-react";

export default function DashboardPage() {
  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
    refetchInterval: 5000,
  });

  const cards = [
    {
      label: "Unternehmen gesamt",
      value: stats?.total_companies ?? 0,
      icon: Building2,
      href: "/jobs",
      gradient: "from-indigo-500/20 to-indigo-500/5",
      iconBg: "from-indigo-500 to-indigo-600",
      glow: "shadow-indigo-500/30",
      text: "text-indigo-300",
    },
    {
      label: "Heute gefunden",
      value: stats?.today_found ?? 0,
      icon: TrendingUp,
      href: "/jobs",
      gradient: "from-emerald-500/20 to-emerald-500/5",
      iconBg: "from-emerald-500 to-emerald-600",
      glow: "shadow-emerald-500/30",
      text: "text-emerald-300",
    },
    {
      label: "Aktive Scrapes",
      value: stats?.active_scrapes ?? 0,
      icon: Activity,
      href: "/scraping",
      gradient: "from-amber-500/20 to-amber-500/5",
      iconBg: "from-amber-500 to-amber-600",
      glow: "shadow-amber-500/30",
      text: "text-amber-300",
    },
    {
      label: "Erfolgsrate",
      value: `${stats?.success_rate ?? 0}%`,
      icon: CheckCircle2,
      href: "/jobs",
      gradient: "from-violet-500/20 to-violet-500/5",
      iconBg: "from-violet-500 to-purple-600",
      glow: "shadow-violet-500/30",
      text: "text-violet-300",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white sm:text-3xl">Übersicht</h1>
          <p className="mt-1 text-sm text-slate-400">
            Deutschlandweit Firmen auswählen und in Echtzeit sammeln.
          </p>
        </div>
        <Link href="/scraping" className="btn-primary hidden sm:inline-flex">
          <Radar className="h-4 w-4" />
          Scraping starten
        </Link>
      </div>

      {/* Stats grid */}
      <div className="stagger grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.label}
              href={card.href}
              className={`card group relative overflow-hidden bg-gradient-to-br ${card.gradient} p-5 transition-transform duration-200 hover:-translate-y-0.5`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-400">{card.label}</p>
                  <p className="mt-2 text-3xl font-bold text-white">{card.value}</p>
                </div>
                <div
                  className={`flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br ${card.iconBg} shadow-lg ${card.glow} transition-transform group-hover:scale-110`}
                >
                  <Icon className={`h-5 w-5 ${card.text}`} />
                </div>
              </div>
              <div className="pointer-events-none absolute -bottom-10 -right-10 h-32 w-32 rounded-full bg-white/[0.03]" />
              <span className="absolute bottom-3 right-4 text-xs font-medium text-slate-500 opacity-0 transition-opacity group-hover:opacity-100">
                Öffnen →
              </span>
            </Link>
          );
        })}
      </div>

      {/* Hero CTA */}
      <div className="card relative overflow-hidden p-6 sm:p-8">
        <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-indigo-600/20 blur-[80px]" />
        <div className="pointer-events-none absolute -bottom-32 -left-24 h-64 w-64 rounded-full bg-purple-600/15 blur-[80px]" />

        <div className="relative flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
          <div className="flex items-start gap-4">
            <div className="relative hidden sm:block">
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 blur-md opacity-50" />
              <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
                <Radar className="h-7 w-7 text-white" />
              </div>
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Neuen Scrape starten</h2>
              <p className="mt-1 max-w-md text-sm text-slate-400">
                Wählen Sie Städte und Kategorien — Ergebnisse werden live
                gestreamt und lassen sich als Excel oder PDF exportieren.
              </p>
            </div>
          </div>
          <Link href="/scraping" className="btn-primary shrink-0">
            Scraping starten
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}