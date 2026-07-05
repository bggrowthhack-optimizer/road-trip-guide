import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import JourneyJob, JourneyRequest, JourneyStatus
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
async def create_journey(request: JourneyRequest) -> JourneyJob:
    job_id = str(uuid.uuid4())
    job = JourneyJob(id=job_id, status=JourneyStatus.queued, request=request)
    _jobs[job_id] = job
    # TODO: поставить в очередь реальную генерацию —
    # discover_route -> geosearch точек -> кеш/генерация контента -> TTS
    return job


@app.get("/api/journey/{job_id}", response_model=JourneyJob)
async def get_journey(job_id: str) -> JourneyJob:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Journey not found")
    return job
