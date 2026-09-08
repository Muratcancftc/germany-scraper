"use client";

import { useState } from "react";
import Link from "next/link";

export default function HistoryPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Historie</h1>
      <div className="card">
        <p className="text-gray-500">Noch keine Historie vorhanden.</p>
        <Link href="/dashboard" className="btn-primary inline-block mt-4">
          Zurück zum Dashboard
        </Link>
      </div>
    </div>
  );
}
