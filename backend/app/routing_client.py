import asyncio
import json
import subprocess
from dataclasses import dataclass
from typing import List, Tuple

from app.geocoding_client import GeoPoint


class RoutingError(Exception):
    pass


@dataclass
class RouteResult:
    coordinates: List[Tuple[float, float]]  # (lon, lat), как в OSRM geojson
    distance_km: float
    duration_min: float


def _fetch_via_curl(url: str, timeout_seconds: float) -> dict:
    """OSRM demo-сервер требует TLS 1.3, а системный Python на этой машине
    линкован со старым LibreSSL 2.8.3, который не может согласовать
    handshake с ним (curl использует другой, современный TLS-стек ОС и
    работает нормально). Пока не решаем это на уровне окружения — просто
    зовём curl подпроцессом для этого конкретного вызова.
    """
    try:
        result = subprocess.run(
            ["curl", "-s", "-f", "--max-time", str(int(timeout_seconds)), url],
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 5,
        )
    except subprocess.TimeoutExpired as e:
        raise RoutingError(f"Сервис маршрутизации не ответил вовремя: {e}") from e

    if result.returncode != 0:
        raise RoutingError(f"curl завершился с кодом {result.returncode}: {result.stderr.strip()}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RoutingError(f"Не удалось разобрать ответ сервиса маршрутизации: {e}") from e


async def get_route(points: List[GeoPoint], base_url: str, timeout_seconds: float = 15.0) -> RouteResult:
    """Геометрия маршрута через OSRM demo-сервер (router.project-osrm.org).
    points — origin, *waypoints, destination, в этом порядке.
    """
    if len(points) < 2:
        raise RoutingError("Нужно минимум две точки для построения маршрута")

    coords_str = ";".join(f"{p.lon},{p.lat}" for p in points)
    url = f"{base_url}/route/v1/driving/{coords_str}?overview=full&geometries=geojson"

    data = await asyncio.to_thread(_fetch_via_curl, url, timeout_seconds)

    if data.get("code") != "Ok":
        raise RoutingError(f"Не удалось построить маршрут: {data.get('code')}")

    routes = data.get("routes") or []
    if not routes:
        raise RoutingError("Сервис маршрутизации не вернул ни одного маршрута")

    route = routes[0]
    coordinates = [(lon, lat) for lon, lat in route["geometry"]["coordinates"]]
    return RouteResult(
        coordinates=coordinates,
        distance_km=route["distance"] / 1000.0,
        duration_min=route["duration"] / 60.0,
    )
