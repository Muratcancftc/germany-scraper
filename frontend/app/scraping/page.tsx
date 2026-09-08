"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCategories, getCities, Category, City } from "@/lib/api/client";
import { useJobStream } from "@/hooks/useJobStream";
import { LiveScrapePanel } from "@/components/scraping/LiveScrapePanel";
import {
  MapPin,
  FolderTree,
  ChevronDown,
  ChevronUp,
  Radar,
  Search,
  Check,
} from "lucide-react";

function SearchBox({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
  return (
    <div className="relative">
      <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input-field pl-10"
      />
    </div>
  );
}

function CitySelect({ items, selected, onToggle }: { items: City[]; selected: number[]; onToggle: (id: number) => void }) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((i) => i.name.toLowerCase().includes(q));
  }, [items, query]);

  return (
    <div className="flex flex-col gap-3">
      <SearchBox value={query} onChange={setQuery} placeholder="Stadt suchen..." />
      <div className="max-h-72 space-y-1 overflow-y-auto pr-1">
        {filtered.length === 0 && (
          <p className="py-6 text-center text-sm text-slate-500">Keine Städte gefunden</p>
        )}
        {filtered.map((item) => {
          const isSel = selected.includes(item.id);
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onToggle(item.id)}
              className={`group flex w-full items-center gap-3 rounded-xl border px-3.5 py-2.5 text-left text-sm transition-all duration-200 ${
                isSel
                  ? "border-indigo-400/40 bg-indigo-500/10 text-indigo-100 shadow-[0_0_20px_rgba(99,102,241,0.15)]"
                  : "border-white/[0.06] bg-white/[0.02] text-slate-300 hover:border-white/15 hover:bg-white/[0.05]"
              }`}
            >
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition-all ${
                  isSel
                    ? "border-indigo-400 bg-gradient-to-br from-indigo-500 to-purple-500 text-white"
                    : "border-slate-600 bg-transparent group-hover:border-slate-400"
                }`}
              >
                {isSel && <Check className="h-3.5 w-3.5" />}
              </span>
              <span className="flex items-center gap-2">
                <MapPin className={`h-3.5 w-3.5 ${isSel ? "text-indigo-300" : "text-slate-500"}`} />
                {item.name}
              </span>
            </button>
          );
        })}
      </div>
      <p className="text-xs font-medium text-slate-400">
        {selected.length} {selected.length === 1 ? "Stadt ausgewählt" : "Städte ausgewählt"}
      </p>
    </div>
  );
}

function CategoryPicker({ categories, selected, onToggle }: { categories: Category[]; selected: number[]; onToggle: (id: number) => void }) {
  const groups = useMemo(() => {
    const map = new Map<string, Category[]>();
    for (const c of categories) {
      const g = c.group || "Sonstige";
      if (!map.has(g)) map.set(g, []);
      map.get(g)!.push(c);
    }
    return Array.from(map.entries());
  }, [categories]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-slate-200">Kategorien</span>
        <button
          type="button"
          onClick={() => categories.forEach((c) => !selected.includes(c.id) && onToggle(c.id))}
          className="text-xs font-medium text-indigo-400 transition-colors hover:text-indigo-300"
        >
          Alle auswählen
        </button>
      </div>

      <div className="space-y-3">
        {groups.map(([group, items]) => {
          const groupSel = items.filter((c) => selected.includes(c.id)).length;
          return (
            <div key={group} className="overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.02]">
              <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-2">
                  <FolderTree className="h-4 w-4 text-violet-400" />
                  <span className="text-sm font-semibold text-slate-200">{group}</span>
                </div>
                <span className="badge bg-white/[0.06] text-slate-300">
                  {groupSel}/{items.length}
                </span>
              </div>
              <div className="space-y-1 border-t border-white/[0.06] p-3">
                {items.map((c) => {
                  const isSel = selected.includes(c.id);
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => onToggle(c.id)}
                      className={`group flex w-full items-start gap-3 rounded-lg border px-3 py-2 text-left text-sm transition-all duration-200 ${
                        isSel
                          ? "border-violet-400/40 bg-violet-500/10 text-violet-100 shadow-[0_0_20px_rgba(139,92,246,0.15)]"
                          : "border-transparent text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
                      }`}
                    >
                      <span
                        className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-all ${
                          isSel
                            ? "border-violet-400 bg-gradient-to-br from-violet-500 to-purple-500 text-white"
                            : "border-slate-600 bg-transparent group-hover:border-slate-400"
                        }`}
                      >
                        {isSel && <Check className="h-3 w-3" />}
                      </span>
                      {c.name}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      <p className="text-xs font-medium text-slate-400">
        {selected.length} {selected.length === 1 ? "Kategorie ausgewählt" : "Kategorien ausgewählt"}
      </p>
    </div>
  );
}

export default function ScrapingPage() {
  const [selectedCities, setSelectedCities] = useState<number[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<number[]>([]);
  const [maxResults, setMaxResults] = useState<string>("");
  const [advanced, setAdvanced] = useState(false);
  const [error, setError] = useState("");
  const { state: stream, start: startStream, reset: resetStream } = useJobStream();

  const { data: cities = [] as City[] } = useQuery({ queryKey: ["cities"], queryFn: getCities });
  const { data: categories = [] as Category[] } = useQuery({ queryKey: ["categories"], queryFn: getCategories });

  const canStart = selectedCities.length > 0 && selectedCategories.length > 0;
  const started = stream.status !== "idle";

  const handleStart = async () => {
    setError("");
    await startStream({
      city_ids: selectedCities,
      category_ids: selectedCategories,
      max_results: maxResults ? Number(maxResults) : undefined,
    });
  };

  if (started) {
    return (
      <div className="space-y-4">
        <LiveScrapePanel state={stream} />
        <button
          onClick={() => {
            resetStream();
            setError("");
          }}
          className="text-sm font-medium text-indigo-400 transition-colors hover:text-indigo-300"
        >
          ← Neuen Scrape starten
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">Neuen Scrape starten</h1>
        <p className="mt-1 text-sm text-slate-400">
          Städte und Kategorien wählen — Ergebnisse erscheinen live.
        </p>
      </div>

      <div className="stagger grid grid-cols-1 gap-5 lg:grid-cols-2">
        <section className="card p-5 sm:p-6">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/20 to-indigo-500/5 ring-1 ring-inset ring-indigo-400/20">
              <MapPin className="h-4 w-4 text-indigo-300" />
            </div>
            <h2 className="text-base font-semibold text-white">Städte</h2>
          </div>
          <CitySelect
            items={cities}
            selected={selectedCities}
            onToggle={(id) =>
              setSelectedCities((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
            }
          />
        </section>

        <section className="card p-5 sm:p-6">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/20 to-violet-500/5 ring-1 ring-inset ring-violet-400/20">
              <FolderTree className="h-4 w-4 text-violet-300" />
            </div>
            <h2 className="text-base font-semibold text-white">Kategorien</h2>
          </div>
          <CategoryPicker
            categories={categories}
            selected={selectedCategories}
            onToggle={(id) =>
              setSelectedCategories((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
            }
          />
        </section>
      </div>

      <section className="card p-5">
        <button
          type="button"
          onClick={() => setAdvanced((v) => !v)}
          className="flex items-center gap-2 text-sm font-medium text-slate-400 transition-colors hover:text-slate-200"
        >
          Erweiterte Einstellungen
          {advanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {advanced && (
          <div className="mt-4 max-w-md">
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Maximale Ergebnisse pro Stadt/Kategorie
            </label>
            <input
              type="number"
              min={1}
              placeholder="0 = unbegrenzt"
              value={maxResults}
              onChange={(e) => setMaxResults(e.target.value)}
              className="input-field"
            />
          </div>
        )}
      </section>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4">
        <button onClick={handleStart} disabled={!canStart} className="btn-primary px-8 py-3">
          <Radar className="h-4 w-4" />
          Scraping starten
        </button>
        {!canStart && (
          <span className="text-sm text-slate-500">
            Bitte mindestens eine Stadt und eine Kategorie auswählen
          </span>
        )}
      </div>
    </div>
  );
}