import type { JourneyJob, JourneyRequest } from "@/types/journey";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function createJourney(request: JourneyRequest): Promise<JourneyJob> {
  const res = await fetch(`${API_BASE}/api/journey`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    throw new Error(`Не удалось создать маршрут: ${res.status}`);
  }
  return res.json();
}

export async function getJourney(id: string): Promise<JourneyJob> {
  const res = await fetch(`${API_BASE}/api/journey/${id}`);
  if (!res.ok) {
    throw new Error(`Маршрут не найден: ${res.status}`);
  }
  return res.json();
}
