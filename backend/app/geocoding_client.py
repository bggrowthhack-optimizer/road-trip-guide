from dataclasses import dataclass

import httpx


class GeocodingError(Exception):
    pass


@dataclass
class GeoPoint:
    lat: float
    lon: float
    label: str


async def geocode(client: httpx.AsyncClient, place_name: str, user_agent: str) -> GeoPoint:
    """Геокодинг через Photon (photon.komoot.io, данные OSM, бесплатно,
    без ключа). Nominatim рассматривался как основной вариант, но при
    проверке вернул "Access denied" с этой машины — Photon отработал
    надёжно, используем его.
    """
    try:
        resp = await client.get(
            "https://photon.komoot.io/api/",
            params={"q": place_name, "limit": 1},
            headers={"User-Agent": user_agent},
        )
    except httpx.HTTPError as e:
        raise GeocodingError(f"Не удалось связаться с геокодером для «{place_name}»: {e}") from e

    if resp.status_code != 200:
        raise GeocodingError(f"Геокодер вернул {resp.status_code} для «{place_name}»")

    data = resp.json()
    features = data.get("features") or []
    if not features:
        raise GeocodingError(f"Не удалось определить координаты: «{place_name}»")

    feature = features[0]
    lon, lat = feature["geometry"]["coordinates"]
    label = feature.get("properties", {}).get("name", place_name)
    return GeoPoint(lat=lat, lon=lon, label=label)
