"use client";

import { useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { getAuthToken } from "@/lib/api/client";
import Sidebar from "@/components/common/Sidebar";
import MobileNav from "@/components/common/MobileNav";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!getAuthToken()) {
      router.replace("/auth/login");
    } else {
      setChecked(true);
    }
  }, [router]);

  if (!checked) {
    return <div className="min-h-screen bg-[#07070b]" />;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <MobileNav />
        <main className="flex-1 overflow-auto px-4 py-6 sm:px-8 sm:py-8">
          <div className="mx-auto w-full max-w-7xl animate-fade-in-up">{children}</div>
        </main>
      </div>
    </div>
  );
}