import asyncio
from dataclasses import dataclass
from typing import List

import httpx

WIKI_API = "https://ru.wikipedia.org/w/api.php"
MAX_RETRIES = 4


class WikipediaError(Exception):
    pass


@dataclass
class WikiCandidate:
    pageid: int
    title: str
    lat: float
    lon: float
    dist_m: float


async def _get_with_retry(client: httpx.AsyncClient, params: dict, user_agent: str) -> httpx.Response:
    """Wikipedia иногда троттлит анонимные запросы после всплеска трафика
    (получили 429 при повторных прогонах во время разработки) — повторяем
    с экспоненциальной паузой, уважая Retry-After, если он есть.
    """
    delay = 2.0
    last_error: Exception = WikipediaError("Неизвестная ошибка")
    for attempt in range(MAX_RETRIES):
        try:
            resp = await client.get(WIKI_API, params=params, headers={"User-Agent": user_agent})
        except httpx.HTTPError as e:
            last_error = WikipediaError(f"Не удалось связаться с Wikipedia: {e}")
            await asyncio.sleep(delay)
            delay *= 2
            continue

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            wait_seconds = float(retry_after) if retry_after and retry_after.isdigit() else delay
            last_error = WikipediaError("Wikipedia вернул 429 (превышен лимит запросов)")
            await asyncio.sleep(wait_seconds)
            delay *= 2
            continue

        if resp.status_code != 200:
            raise WikipediaError(f"Wikipedia вернул {resp.status_code}")

        return resp

    raise last_error


async def geosearch(
    client: httpx.AsyncClient,
    lat: float,
    lon: float,
    user_agent: str,
    radius_m: int = 7000,
    limit: int = 15,
) -> List[WikiCandidate]:
    resp = await _get_with_retry(
        client,
        {
            "action": "query",
            "list": "geosearch",
            "gscoord": f"{lat}|{lon}",
            "gsradius": radius_m,
            "gslimit": limit,
            "format": "json",
        },
        user_agent,
    )
    results = resp.json().get("query", {}).get("geosearch", [])
    return [
        WikiCandidate(
            pageid=r["pageid"],
            title=r["title"],
            lat=r["lat"],
            lon=r["lon"],
            dist_m=r["dist"],
        )
        for r in results
    ]


async def fetch_extract(client: httpx.AsyncClient, pageid: int, user_agent: str) -> str:
    """Возвращает plain-text intro статьи. Пустая строка, если статьи нет
    или у неё нет содержимого — это штатный случай, не ошибка сети.
    """
    resp = await _get_with_retry(
        client,
        {
            "action": "query",
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "pageids": pageid,
            "format": "json",
        },
        user_agent,
    )
    pages = resp.json().get("query", {}).get("pages", {})
    page = pages.get(str(pageid), {})
    return page.get("extract", "") or ""


def wiki_url(title: str) -> str:
    return f"https://ru.wikipedia.org/wiki/{title.replace(' ', '_')}"
