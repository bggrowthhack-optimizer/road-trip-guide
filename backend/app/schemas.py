from enum import Enum

from pydantic import BaseModel, Field


class TransportMode(str, Enum):
    car = "car"
    train = "train"
    walk = "walk"
    flight = "flight"


class JourneyRequest(BaseModel):
    origin: str = Field(..., description="Точка старта, свободный текст")
    destination: str = Field(..., description="Точка финиша, свободный текст")
    waypoints: list[str] = Field(default_factory=list, description="Промежуточные точки, опционально")
    mode: TransportMode = TransportMode.car


class JourneyStatus(str, Enum):
    queued = "queued"
    discovering_route = "discovering_route"
    generating_content = "generating_content"
    ready = "ready"
    failed = "failed"


class JourneyJob(BaseModel):
    id: str
    status: JourneyStatus
    request: JourneyRequest
