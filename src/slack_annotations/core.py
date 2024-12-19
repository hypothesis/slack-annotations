import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from .format import format_annotations

SEARCH_HOURS = 1


def notify(
    search_params: dict[str, Any] | None = None,
    token: str | None = None,
    cache_path: str | None = None,
    group_name: str | None = None,
) -> str:
    search_params = _make_search_params(search_params, cache_path)
    headers = _make_headers(token)

    annotations = _fetch_annotations(search_params, headers)

    _maybe_update_cache(annotations, cache_path)
    return format_annotations(annotations, group_name)


def _make_search_params(
    params: dict[str, Any] | None = None, cache_path: str | None = None
) -> dict[str, Any]:
    # Deliberately override any given sort or order param as these specific
    # values are needed for the algorithm below to work.
    default_params = {
        "sort": "created",
        "order": "asc",
        "search_after": _get_search_after(cache_path),
    }
    if params:
        default_params.update(params)
    return default_params


def _make_headers(token: str | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _get_search_after(cache_path: str | None = None) -> str:
    """Return the search_after value from the cache file or the default."""
    default = (datetime.now(UTC) - timedelta(hours=SEARCH_HOURS)).isoformat()

    if not cache_path:
        return default

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return max(default, json.load(f)["search_after"])
    except FileNotFoundError:
        return default


def _maybe_update_cache(
    annotations: list[dict[str, Any]], cache_path: str | None = None
) -> None:
    """Update the cache file with created timestamp of the last annotation."""
    if not annotations or not cache_path:
        return

    search_after = annotations[-1]["created"]
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({"search_after": search_after}, f)


def _fetch_annotations(
    params: dict[str, Any], headers: dict[str, str]
) -> list[dict[str, Any]]:
    return (
        httpx.get("https://hypothes.is/api/search", params=params, headers=headers)
        .raise_for_status()
        .json()["rows"]
    )
