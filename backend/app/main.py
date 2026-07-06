import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.route_discovery import discover_route_and_points
from app.schemas import JourneyJob, JourneyRequest, JourneyStatus, SubmitSummariesRequest
from app.settings import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory заглушка вместо БД — заменить на постоянное хранилище
# (Postgres, см. ARCHITECTURE.md) при переходе от скелета к MVP.
_jobs: dict[str, JourneyJob] = {}


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/journey", response_model=JourneyJob)
async def create_journey(request: JourneyRequest, background_tasks: BackgroundTasks) -> JourneyJob:
    job_id = str(uuid.uuid4())
    job = JourneyJob(id=job_id, status=JourneyStatus.queued, request=request)
    _jobs[job_id] = job
    background_tasks.add_task(discover_route_and_points, job_id, _jobs)
    return job


@app.get("/api/journey/{job_id}", response_model=JourneyJob)
async def get_journey(job_id: str) -> JourneyJob:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Journey not found")
    return job


@app.post("/api/journey/{job_id}/summaries", response_model=JourneyJob)
async def submit_summaries(job_id: str, body: SubmitSummariesRequest) -> JourneyJob:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Journey not found")
    if job.status != JourneyStatus.awaiting_manual_summary:
        raise HTTPException(
            status_code=409,
            detail=f"Job in status {job.status}, not awaiting_manual_summary",
        )

    by_pageid = {entry.pageid: entry.summary for entry in body.summaries}
    for point in job.points or []:
        if point.pageid in by_pageid:
            point.summary = by_pageid[point.pageid]

    if job.points and all(p.summary for p in job.points):
        job.status = JourneyStatus.ready

    return job
