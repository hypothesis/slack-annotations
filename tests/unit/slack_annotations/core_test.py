import json
from datetime import UTC, datetime, timedelta

import httpx
from freezegun import freeze_time

from src.slack_annotations.core import (
    SEARCH_HOURS,
    _fetch_annotations,
    _get_search_after,
    _init_search_params,
    _update_cache,
)


@freeze_time("2024-12-01T01:00:00+00:00")
def test_init_search_params():
    params = _init_search_params({"some_key": "some_value"})

    assert params == {
        "some_key": "some_value",
        "sort": "created",
        "order": "asc",
        "search_after": (datetime.now(UTC) - timedelta(hours=SEARCH_HOURS)).isoformat(),
    }


def test_get_search_after(tmp_path):
    cache_path = tmp_path / "cache.json"
    default = "2024-12-01T00:00:00+00:00"
    search_after = "2024-12-01T00:30:00+00:00"
    cache_path.write_text(json.dumps({"search_after": "2024-12-01T00:30:00+00:00"}))

    assert _get_search_after(str(cache_path), default) == search_after


def test_update_cache(tmp_path):
    cache_path = tmp_path / "cache.json"
    search_after = "2024-12-01T00:30:00+00:00"

    _update_cache(str(cache_path), search_after)

    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["search_after"] == search_after


def test_fetch_annotations(httpx_mock):
    annotations = {"rows": [{"id": 1, "created": "2024-12-01T00:00:00+00:00"}]}
    params = {"param1": "value1"}
    headers = {"Authorization": "Bearer test_token"}
    httpx_mock.add_response(
        url=httpx.URL("https://hypothes.is/api/search", params=params),
        content=json.dumps(annotations),
        match_headers=headers,
    )

    result = _fetch_annotations(params, headers)

    assert result == annotations["rows"]
