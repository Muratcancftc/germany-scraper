"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCategories, getCities, Category, City } from "@/lib/api/client";
import { useJobStream } from "@/hooks/useJobStream";
import { LiveScrapePanel } from "@/components/scraping/LiveScrapePanel";

function CitySelect({
  items,
  selected,
  onToggle,
}: {
  items: City[];
  selected: number[];
  onToggle: (id: number) => void;
}) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((i) => i.name.toLowerCase().includes(q));
  }, [items, query]);

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-semibold text-gray-700">Städte</label>
      <input
        type="text"
        placeholder="Suchen..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
      />
      <div className="border border-gray-200 rounded-lg max-h-72 overflow-y-auto">
        {filtered.length === 0 && <p className="p-4 text-sm text-gray-400">Keine Ergebnisse</p>}
        {filtered.map((item) => (
          <label key={item.id} className="flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-gray-50">
            <input
              type="checkbox"
              checked={selected.includes(item.id)}
              onChange={() => onToggle(item.id)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600"
            />
            <span className="text-sm">{item.name}</span>
          </label>
        ))}
      </div>
      <p className="text-xs text-gray-500">{selected.length} ausgewählt</p>
    </div>
  );
}

function CategoryPicker({
  categories,
  selected,
  onToggle,
}: {
  categories: Category[];
  selected: number[];
  onToggle: (id: number) => void;
}) {
  const groups = useMemo(() => {
    const map = new Map<string, Category[]>();
    for (const c of categories) {
      const g = c.group || "Sonstige";
      if (!map.has(g)) map.set(g, []);
      map.get(g)!.push(c);
    }
    return Array.from(map.entries());
  }, [categories]);

  const groupIds = (items: Category[]) => items.map((c) => c.id);
  const allGroupSelected = (items: Category[]) =>
    items.length > 0 && items.every((c) => selected.includes(c.id));

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-gray-700">Kategorien</label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => categories.forEach((c) => !selected.includes(c.id) && onToggle(c.id))}
            className="text-xs text-blue-600 hover:underline"
          >
            Alle auswählen
          </button>
          <button
            type="button"
            onClick={() => categories.forEach((c) => selected.includes(c.id) && onToggle(c.id))}
            className="text-xs text-gray-500 hover:underline"
          >
            Keine
          </button>
        </div>
      </div>

      <div className="border border-gray-200 rounded-lg divide-y">
        {groups.map(([group, items]) => {
          const allSel = allGroupSelected(items);
          return (
            <div key={group} className="p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-gray-800">{group}</span>
                <button
                  type="button"
                  onClick={() =>
                    allSel
                      ? items.forEach((c) => onToggle(c.id))
                      : items.forEach((c) => !selected.includes(c.id) && onToggle(c.id))
                  }
                  className="text-xs text-blue-600 hover:underline"
                >
                  {allSel ? "Alle abwählen" : "Alle auswählen"}
                </button>
              </div>
              <div className="grid gap-1">
                {items.map((c) => (
                  <label key={c.id} className="flex items-center gap-3 px-2 py-1.5 cursor-pointer hover:bg-gray-50 rounded">
                    <input
                      type="checkbox"
                      checked={selected.includes(c.id)}
                      onChange={() => onToggle(c.id)}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600"
                    />
                    <span className="text-sm">{c.name}</span>
                  </label>
                ))}
              </div>
            </div>
          );
        })}
      </div>
      <p className="text-xs text-gray-500">{selected.length} ausgewählt</p>
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
  const { data: categories = [] as Category[] } = useQuery({
    queryKey: ["categories"],
    queryFn: getCategories,
  });

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
      <div className="max-w-7xl mx-auto">
        <LiveScrapePanel state={stream} />
        <div className="mt-6">
          <button
            onClick={() => {
              resetStream();
              setError("");
            }}
            className="text-blue-600 hover:underline text-sm"
          >
            Neuen Scrape starten
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Neuen Scrape starten</h1>
      <p className="text-gray-500 mb-6">
        Wählen Sie Städte und Kategorien aus, um passende Unternehmen zu scrapen.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <CitySelect items={cities} selected={selectedCities} onToggle={(id) =>
            setSelectedCities((prev) =>
              prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
            )
          } />
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <CategoryPicker
            categories={categories}
            selected={selectedCategories}
            onToggle={(id) =>
              setSelectedCategories((prev) =>
                prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
              )
            }
          />
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mt-6">
        <button
          type="button"
          onClick={() => setAdvanced((v) => !v)}
          className="text-sm font-medium text-gray-600 hover:text-gray-900"
        >
          {advanced ? "▲" : "▼"} Erweiterte Einstellungen
        </button>
        {advanced && (
          <div className="mt-4 max-w-md">
            <label className="text-sm font-semibold text-gray-700">
              Maximale Ergebnisse pro Stadt/Kategorie
            </label>
            <input
              type="number"
              min={1}
              placeholder="0 = unbegrenzt"
              value={maxResults}
              onChange={(e) => setMaxResults(e.target.value)}
              className="mt-1 w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        )}
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-6 flex items-center gap-3">
        <button
          onClick={handleStart}
          disabled={!canStart}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Scraping starten
        </button>
        {!canStart && (
          <span className="text-sm text-gray-400">
            Bitte mindestens eine Stadt und eine Kategorie auswählen
          </span>
        )}
      </div>
    </div>
  );
}
