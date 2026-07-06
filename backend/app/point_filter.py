"""Фильтрация точек, найденных через Wikipedia geosearch.

Сырой geosearch рядом с крупными городами возвращает слишком много
локального шума (отдельные улицы, дома) — на маршруте Ульяновск-Самара
(248 км) вернулось 263 точки вместо ожидаемых 15-30 разумных.

Сейчас — эвристики без внешних ключей (длина статьи + паттерны в
названии). Когда появится ключ Yandex Maps/Cloud — сюда добавляется
`YandexClassifierFilter`, который для каждой точки спрашивает Yandex
Geocoder (`kind` в ответе: locality/street/house/...) и отбрасывает
всё, что классифицируется как street/house — это точнее эвристик, но
требует лишнего API-вызова на точку и рабочего ключа. Интерфейс
(`filter_points`) при этом не меняется — вызывающий код (route_discovery.py)
не должен знать, какая реализация фильтра сейчас используется.
"""

import re
from typing import List

from app.wikipedia_client import WikiCandidate

MIN_EXTRACT_LENGTH = 400

_EXCLUDE_TITLE_PATTERNS = [
    r"\bулица\b", r"\bпереулок\b", r"\bпроспект\b", r"\bшоссе\b",
    r"\bплощадь\b", r"\bбульвар\b", r"\bсквер\b", r"\bмикрорайон\b",
    r"\bстанция\b", r"\bплатформа\b", r"\bразъезд\b",
    # административные единицы — не конкретные достопримечательности,
    # а абстрактные территории, для рассказа-точки на маршруте не годятся
    r"\bобласть\b", r"\bрайон\b", r"\bсельское поселение\b",
    r"\bгородской округ\b", r"\bмуниципальн\w+ образовани\w+\b",
]
_EXCLUDE_TITLE_RE = re.compile("|".join(_EXCLUDE_TITLE_PATTERNS), re.IGNORECASE)


def is_likely_relevant(title: str, extract: str) -> bool:
    """Эвристический фильтр: True, если точку стоит оставить в маршруте."""
    if _EXCLUDE_TITLE_RE.search(title):
        return False
    if len(extract) < MIN_EXTRACT_LENGTH:
        return False
    return True


def filter_points(candidates_with_extract: List[tuple]) -> List[tuple]:
    """candidates_with_extract — список (position_km, WikiCandidate, extract).
    Возвращает тот же формат, отфильтрованный.
    """
    return [
        (pos, cand, extract)
        for pos, cand, extract in candidates_with_extract
        if is_likely_relevant(cand.title, extract)
    ]
