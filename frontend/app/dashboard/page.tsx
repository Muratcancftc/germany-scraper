"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { getDashboardStats, DashboardStats } from "@/lib/api/client";

export default function DashboardPage() {
  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
    refetchInterval: 5000,
  });

  const cards = [
    { label: "Gesamte Unternehmen", value: stats?.total_companies ?? 0 },
    { label: "Heute gefunden", value: stats?.today_found ?? 0 },
    { label: "Aktive Scrapes", value: stats?.active_scrapes ?? 0 },
    { label: "Erfolgsrate", value: `${stats?.success_rate ?? 0}%` },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Übersicht</h1>
      <p className="text-gray-500 mb-6">Willkommen im Germany Company Scraper Dashboard</p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {cards.map((card) => (
          <div key={card.label} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <p className="text-sm text-gray-500">{card.label}</p>
            <p className="text-3xl font-bold mt-1">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <h2 className="text-lg font-semibold mb-2">Neuen Scrape starten</h2>
        <p className="text-gray-500 mb-6">
          Wählen Sie Städte und Kategorien aus, um Unternehmen in Deutschland zu scrapen.
        </p>
        <Link
          href="/scraping"
          className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          Scraping starten
        </Link>
      </div>
    </div>
  );
}
