"use client";

import { useState } from "react";
import { createJourney } from "@/lib/api";
import type { JourneyJob, TransportMode } from "@/types/journey";

const MODES: { value: TransportMode; label: string; enabled: boolean }[] = [
  { value: "car", label: "Машина", enabled: true },
  { value: "train", label: "Поезд", enabled: false },
  { value: "walk", label: "Прогулка", enabled: false },
  { value: "flight", label: "Самолёт", enabled: false },
];

export default function Home() {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [mode, setMode] = useState<TransportMode>("car");
  const [job, setJob] = useState<JourneyJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await createJourney({ origin, destination, waypoints: [], mode });
      setJob(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Что-то пошло не так");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center bg-zinc-50 px-6 py-16 dark:bg-black">
      <main className="w-full max-w-md">
        <h1 className="mb-2 text-2xl font-semibold tracking-tight text-black dark:text-zinc-50">
          Roadcast
        </h1>
        <p className="mb-8 text-sm text-zinc-600 dark:text-zinc-400">
          Назови маршрут — соберём историю мест по пути, которую можно читать
          или слушать.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex gap-2">
            {MODES.map((m) => (
              <button
                key={m.value}
                type="button"
                disabled={!m.enabled}
                onClick={() => setMode(m.value)}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                  mode === m.value
                    ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black"
                    : "border-zinc-300 text-zinc-500 dark:border-zinc-700"
                } ${!m.enabled ? "cursor-not-allowed opacity-40" : ""}`}
              >
                {m.label}
              </button>
            ))}
          </div>

          <input
            className="rounded-lg border border-zinc-300 px-4 py-3 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            placeholder="Откуда"
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            required
          />
          <input
            className="rounded-lg border border-zinc-300 px-4 py-3 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            placeholder="Куда"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            required
          />

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-black px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:opacity-50 dark:bg-white dark:text-black"
          >
            {loading ? "Собираем..." : "Собрать историю пути"}
          </button>
        </form>

        {error && (
          <p className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}

        {job && (
          <div className="mt-6 rounded-lg border border-zinc-200 p-4 text-sm dark:border-zinc-800">
            <p className="font-medium text-black dark:text-zinc-50">
              Job создан: {job.id}
            </p>
            <p className="text-zinc-500">Статус: {job.status}</p>
            <p className="mt-2 text-zinc-400">
              Генерация ещё не реализована — это только каркас запроса/ответа.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
