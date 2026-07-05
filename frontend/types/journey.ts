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
  | "generating_content"
  | "ready"
  | "failed";

export interface JourneyJob {
  id: string;
  status: JourneyStatus;
  request: JourneyRequest;
}
