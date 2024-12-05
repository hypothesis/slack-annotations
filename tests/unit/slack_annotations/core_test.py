from datetime import datetime, timedelta, UTC
from src.slack_annotations.core import _init_search_params, SEARCH_HOURS


def test_init_search_params():
    params = _init_search_params({"some_key": "some_value"})
    assert params == {
        "some_key": "some_value",
        "sort": "created",
        "order": "asc",
        "search_after": (datetime.now(UTC) - timedelta(hours=SEARCH_HOURS)).isoformat(),
    }
