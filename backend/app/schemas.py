from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TransportMode(str, Enum):
    car = "car"
    train = "train"
    walk = "walk"
    flight = "flight"


class JourneyRequest(BaseModel):
    origin: str = Field(..., description="Точка старта, свободный текст")
    destination: str = Field(..., description="Точка финиша, свободный текст")
    waypoints: List[str] = Field(default_factory=list, description="Промежуточные точки, опционально")
    mode: TransportMode = TransportMode.car


class JourneyStatus(str, Enum):
    queued = "queued"
    discovering_route = "discovering_route"
    awaiting_manual_summary = "awaiting_manual_summary"
    generating_content = "generating_content"
    ready = "ready"
    failed = "failed"


class RoutePoint(BaseModel):
    pageid: int
    title: str
    lat: float
    lon: float
    distance_km: float
    wiki_extract: str
    wiki_url: str
    summary: Optional[str] = None


class JourneyJob(BaseModel):
    id: str
    status: JourneyStatus
    request: JourneyRequest
    points: Optional[List[RoutePoint]] = None
    error: Optional[str] = None


class SummaryEntry(BaseModel):
    pageid: int
    summary: str


class SubmitSummariesRequest(BaseModel):
    summaries: List[SummaryEntry]
