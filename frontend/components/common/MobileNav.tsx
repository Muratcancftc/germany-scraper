"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils/utils";
import { Radar, LayoutDashboard, LogOut, Plus } from "lucide-react";

const items = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/scraping", label: "Scraping", icon: Plus },
];

export default function MobileNav() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between border-b border-white/[0.06] bg-[#07070b]/80 px-4 py-3 backdrop-blur-xl md:hidden">
      <Link href="/dashboard" className="flex items-center gap-2">
        <div className="relative">
          <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 blur-md opacity-60" />
          <div className="relative flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600">
            <Radar className="h-4 w-4 text-white" />
          </div>
        </div>
        <span className="text-sm font-bold text-white">Germany Scraper</span>
      </Link>
      <div className="flex items-center gap-1">
        {items.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-lg p-2 transition-colors",
                active ? "bg-indigo-500/20 text-indigo-300" : "text-slate-500"
              )}
            >
              <Icon className="h-5 w-5" />
            </Link>
          );
        })}
        <button
          onClick={() => {
            localStorage.removeItem("token");
            router.replace("/auth/login");
          }}
          className="rounded-lg p-2 text-slate-500 transition-colors hover:text-red-400"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}