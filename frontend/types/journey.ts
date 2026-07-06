export type TransportMode = "car" | "train" | "walk" | "flight";

export interface JourneyRequest {
  origin: string;
  destination: string;
  waypoints: string[];
  mode: TransportMode;
}

export type JourneyStatus =
  | "queued"
  | "discovering_route"
  | "awaiting_manual_summary"
  | "generating_content"
  | "ready"
  | "failed";

export interface RoutePoint {
  pageid: number;
  title: string;
  lat: number;
  lon: number;
  distance_km: number;
  wiki_extract: string;
  wiki_url: string;
  summary: string | null;
}

export interface JourneyJob {
  id: string;
  status: JourneyStatus;
  request: JourneyRequest;
  points: RoutePoint[] | null;
  error: string | null;
}
