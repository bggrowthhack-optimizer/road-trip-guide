import asyncio
from typing import Dict, List

import httpx

from app.geo_utils import sample_route
from app.geocoding_client import GeocodingError, geocode
from app.point_filter import filter_points
from app.routing_client import RoutingError, get_route
from app.schemas import JourneyJob, JourneyStatus, RoutePoint
from app.settings import settings
from app.wikipedia_client import WikiCandidate, WikipediaError, fetch_extract, geosearch, wiki_url


async def discover_route_and_points(job_id: str, jobs: Dict[str, JourneyJob]) -> None:
    """Оркестратор: geocode -> маршрут -> сэмплирование -> geosearch по
    Wikipedia -> дедуп -> extracts. Заполняет job.points и переводит
    статус в awaiting_manual_summary (текст резюме пишется вручную через
    /summaries, пока нет ключа LLM). Любая необработанная ошибка переводит
    job в failed с понятным сообщением — job не должен зависать молча.
    """
    job = jobs.get(job_id)
    if job is None:
        return

    try:
        job.status = JourneyStatus.discovering_route

        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            place_names = [job.request.origin, *job.request.waypoints, job.request.destination]
            geo_points = []
            for name in place_names:
                geo_points.append(await geocode(client, name, settings.http_user_agent))

            route = await get_route(geo_points, settings.osrm_base_url, settings.http_timeout_seconds)

            samples = sample_route(route.coordinates, step_km=settings.route_sample_step_km)

            semaphore = asyncio.Semaphore(3)

            async def search_one(sample):
                async with semaphore:
                    candidates = await geosearch(
                        client,
                        sample.lat,
                        sample.lon,
                        settings.http_user_agent,
                        radius_m=settings.wikipedia_geosearch_radius_m,
                    )
                    return sample, candidates

            results = await asyncio.gather(*(search_one(s) for s in samples))

            # Дедуп по pageid: для каждой уникальной точки запоминаем
            # минимальную (distance_km сэмпла + расстояние до точки) —
            # это и определяет порядок точки вдоль маршрута.
            best_by_pageid: Dict[int, tuple] = {}
            for sample, candidates in results:
                candidate: WikiCandidate
                for candidate in candidates:
                    position_km = sample.distance_km + candidate.dist_m / 1000.0
                    existing = best_by_pageid.get(candidate.pageid)
                    if existing is None or position_km < existing[0]:
                        best_by_pageid[candidate.pageid] = (position_km, candidate)

            ordered = sorted(best_by_pageid.values(), key=lambda pair: pair[0])

            async def fetch_one(position_km: float, candidate: WikiCandidate):
                async with semaphore:
                    extract = await fetch_extract(client, candidate.pageid, settings.http_user_agent)
                return (position_km, candidate, extract)

            with_extracts = await asyncio.gather(
                *(fetch_one(pos, cand) for pos, cand in ordered)
            )

            # Сырой geosearch рядом с крупными городами возвращает слишком
            # много локального шума (отдельные улицы, дома) — фильтруем
            # эвристиками (см. point_filter.py). Точка подключения для
            # будущей замены на Yandex-классификацию, когда появится ключ.
            filtered = filter_points(list(with_extracts))

            points: List[RoutePoint] = [
                RoutePoint(
                    pageid=candidate.pageid,
                    title=candidate.title,
                    lat=candidate.lat,
                    lon=candidate.lon,
                    distance_km=round(position_km, 1),
                    wiki_extract=extract,
                    wiki_url=wiki_url(candidate.title),
                )
                for position_km, candidate, extract in filtered
            ]

        job.points = points
        job.status = JourneyStatus.awaiting_manual_summary

    except (GeocodingError, RoutingError, WikipediaError) as e:
        job.status = JourneyStatus.failed
        job.error = str(e)
    except Exception as e:  # noqa: BLE001 - последний рубеж, job не должен зависать
        job.status = JourneyStatus.failed
        job.error = f"Неожиданная ошибка: {e}"
