"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/scraping", label: "Scraping", icon: "🔍" },
  { href: "/jobs", label: "Ergebnisse", icon: "📋" },
  { href: "/historie", label: "Historie", icon: "📜" },
  { href: "/einstellungen", label: "Einstellungen", icon: "⚙️" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-xl font-bold">🇩🇪 Scraper</h1>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "block px-4 py-3 rounded-lg text-sm font-medium transition-colors",
              pathname === item.href
                ? "bg-primary-600 text-white"
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            )}
          >
            <span className="mr-2">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-700">
        <div className="text-xs text-gray-400">
          <p>v1.0.0</p>
          <p>© 2026 Germany Scraper</p>
        </div>
      </div>
    </aside>
  );
}
