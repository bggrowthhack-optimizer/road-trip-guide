"use client";

import { useEffect, useRef, useState } from "react";
import { createJourney, getJourney } from "@/lib/api";
import type { JourneyJob, TransportMode } from "@/types/journey";

const MODES: { value: TransportMode; label: string; enabled: boolean }[] = [
  { value: "car", label: "Машина", enabled: true },
  { value: "train", label: "Поезд", enabled: false },
  { value: "walk", label: "Прогулка", enabled: false },
  { value: "flight", label: "Самолёт", enabled: false },
];

const STATUS_LABELS: Record<string, string> = {
  queued: "В очереди…",
  discovering_route: "Строим маршрут и ищем точки…",
  awaiting_manual_summary: "Точки найдены, ждём резюме…",
  generating_content: "Собираем рассказы…",
  ready: "Готово",
  failed: "Не получилось",
};

export default function Home() {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [mode, setMode] = useState<TransportMode>("car");
  const [job, setJob] = useState<JourneyJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  function startPolling(id: string) {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const updated = await getJourney(id);
        setJob(updated);
        // awaiting_manual_summary — не финальное состояние: резюме могут
        // прийти позже (вручную через /summaries), поэтому продолжаем
        // поллинг и здесь, останавливаемся только на ready/failed.
        if (["ready", "failed"].includes(updated.status)) {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch (err) {
        if (pollRef.current) clearInterval(pollRef.current);
        setError(err instanceof Error ? err.message : "Ошибка при опросе статуса");
      }
    }, 2000);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setJob(null);
    setLoading(true);
    try {
      const result = await createJourney({ origin, destination, waypoints: [], mode });
      setJob(result);
      startPolling(result.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Что-то пошло не так");
    } finally {
      setLoading(false);
    }
  }

  const isPolling = job && ["queued", "discovering_route"].includes(job.status);

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
            disabled={loading || !!isPolling}
            className="rounded-lg bg-black px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:opacity-50 dark:bg-white dark:text-black"
          >
            {loading || isPolling ? "Собираем..." : "Собрать историю пути"}
          </button>
        </form>

        {error && (
          <p className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}

        {job && (
          <div className="mt-6">
            <p className="mb-4 text-sm font-medium text-zinc-500 dark:text-zinc-400">
              {STATUS_LABELS[job.status] ?? job.status}
            </p>

            {job.status === "failed" && job.error && (
              <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
                {job.error}
              </p>
            )}

            {job.points && job.points.length > 0 && (
              <ul className="flex flex-col gap-3">
                {job.points.map((point) => (
                  <li
                    key={point.pageid}
                    className="rounded-lg border border-zinc-200 p-4 text-sm dark:border-zinc-800"
                  >
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <span className="font-medium text-black dark:text-zinc-50">
                        {point.title}
                      </span>
                      <span className="shrink-0 rounded-full bg-zinc-900 px-2 py-0.5 text-xs font-semibold text-white dark:bg-white dark:text-black">
                        {point.distance_km} км
                      </span>
                    </div>
                    <p className="text-zinc-600 dark:text-zinc-400">
                      {point.summary ?? (point.wiki_extract || "Текст ещё не готов.")}
                    </p>
                    <a
                      href={point.wiki_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-block text-xs text-zinc-400 underline"
                    >
                      Wikipedia
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
