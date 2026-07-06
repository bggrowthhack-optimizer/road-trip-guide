import math
from dataclasses import dataclass
from typing import List, Tuple


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние по большому кругу между двумя точками в километрах."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@dataclass
class RouteSample:
    lat: float
    lon: float
    distance_km: float


def sample_route(coordinates: List[Tuple[float, float]], step_km: float = 5.0) -> List[RouteSample]:
    """Проходит по геометрии маршрута (список (lon, lat), как отдаёт OSRM
    geojson), накапливая расстояние по haversine, и возвращает точки через
    каждые step_km, плюс всегда первую и последнюю точку маршрута.
    """
    if not coordinates:
        return []

    samples: List[RouteSample] = []
    lon0, lat0 = coordinates[0]
    samples.append(RouteSample(lat=lat0, lon=lon0, distance_km=0.0))

    cumulative_km = 0.0
    next_threshold_km = step_km
    prev_lon, prev_lat = lon0, lat0

    for lon, lat in coordinates[1:]:
        segment_km = haversine_km(prev_lat, prev_lon, lat, lon)
        cumulative_km += segment_km
        while cumulative_km >= next_threshold_km:
            samples.append(RouteSample(lat=lat, lon=lon, distance_km=next_threshold_km))
            next_threshold_km += step_km
        prev_lon, prev_lat = lon, lat

    last_lon, last_lat = coordinates[-1]
    if not samples or samples[-1].distance_km < cumulative_km:
        samples.append(RouteSample(lat=last_lat, lon=last_lon, distance_km=cumulative_km))

    return samples
