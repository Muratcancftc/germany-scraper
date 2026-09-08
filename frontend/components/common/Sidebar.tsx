"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils/utils";
import {
  LayoutDashboard,
  Radar,
  Building2,
  History,
  Settings,
  LogOut,
  Zap,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/scraping", label: "Scraping", icon: Radar },
  { href: "/jobs", label: "Ergebnisse", icon: Building2 },
  { href: "/historie", label: "Historie", icon: History },
  { href: "/einstellungen", label: "Einstellungen", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.replace("/auth/login");
  };

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-white/[0.06] bg-white/[0.02] backdrop-blur-2xl md:flex">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5">
        <div className="relative">
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 blur-md opacity-60" />
          <div className="relative flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
            <Radar className="h-5 w-5 text-white" />
          </div>
        </div>
        <div>
          <h1 className="text-sm font-bold leading-tight text-white">
            Germany <span className="text-gradient">Scraper</span>
          </h1>
          <p className="flex items-center gap-1 text-[11px] text-slate-500">
            <Zap className="h-3 w-3 text-amber-400" /> Pro Panel
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active =
            pathname === item.href ||
            (item.href === "/jobs" && pathname.startsWith("/scraping/"));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200",
                active
                  ? "text-white"
                  : "text-slate-400 hover:bg-white/[0.04] hover:text-white"
              )}
            >
              {active && (
                <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-indigo-500/20 to-purple-500/10 ring-1 ring-inset ring-indigo-400/30" />
              )}
              <Icon
                className={cn(
                  "relative z-10 h-[18px] w-[18px] transition-colors",
                  active ? "text-indigo-300" : "text-slate-500 group-hover:text-slate-300"
                )}
              />
              <span className="relative z-10">{item.label}</span>
              {active && <span className="absolute right-3 z-10 h-1.5 w-1.5 rounded-full bg-indigo-400 shadow-[0_0_8px_rgba(99,102,241,0.8)]" />}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-white/[0.06] px-3 py-4">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium text-slate-400 transition-all hover:bg-red-500/10 hover:text-red-300"
        >
          <LogOut className="h-[18px] w-[18px]" />
          Abmelden
        </button>
        <p className="mt-3 px-3.5 text-[11px] text-slate-600">v1.0 · Vercel Pro · Fluid Compute</p>
      </div>
    </aside>
  );
}