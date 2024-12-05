from datetime import datetime, timedelta, UTC
from src.slack_annotations.core import _init_search_params, SEARCH_HOURS, _get_search_after
import json
from freezegun import freeze_time


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
