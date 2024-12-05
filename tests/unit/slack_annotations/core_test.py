import json
from datetime import UTC, datetime, timedelta

from freezegun import freeze_time

from src.slack_annotations import core


@freeze_time("2024-12-01T01:00:00+00:00")
def test_init_search_params():
    params = core._init_search_params({"some_key": "some_value"})

    assert params == {
        "some_key": "some_value",
        "sort": "created",
        "order": "asc",
        "search_after": (datetime.now(UTC) - timedelta(hours=core.SEARCH_HOURS)).isoformat(),
    }


def test_get_search_after(tmp_path):
    cache_path = tmp_path / "cache.json"
    default = "2024-12-01T00:00:00+00:00"
    search_after = "2024-12-01T00:30:00+00:00"
    cache_path.write_text(json.dumps({"search_after": "2024-12-01T00:30:00+00:00"}))

    assert core._get_search_after(str(cache_path), default) == search_after


def test_update_cache(tmp_path):
    cache_path = tmp_path / "cache.json"
    search_after = "2024-12-01T00:30:00+00:00"

    core._update_cache(str(cache_path), search_after)

    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["search_after"] == search_after
