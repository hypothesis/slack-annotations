import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from freezegun import freeze_time

from src.slack_annotations.core import (
    SEARCH_HOURS,
    _fetch_annotations,
    _format_annotations,
    _get_search_after,
    _init_search_params,
    _update_cache, notify,
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


def test_format_annotations(search_annotations, slack_annotations):
    assert _format_annotations(search_annotations["rows"]) == json.dumps(slack_annotations)


@freeze_time("2024-12-01T01:00:00+00:00")
def test_default_notify(search_annotations, slack_annotations, httpx_mock):
    search_after = (datetime.now(UTC) - timedelta(hours=SEARCH_HOURS)).isoformat()
    params = {
        "sort": "created",
        "order": "asc",
        "search_after": search_after,
    }
    httpx_mock.add_response(
        url=httpx.URL("https://hypothes.is/api/search", params=params),
        content=json.dumps(search_annotations),
    )

    assert notify() == json.dumps(slack_annotations)


@pytest.fixture
def slack_annotations():
    return {
        "text": "A new annotation was posted",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "`test_user_1` (md............................) annotated <https://example.com/|Annotating the law | Hypothes.is>:",
                },
                "fields": [
                    {"type": "mrkdwn", "text": "*Quote:*"},
                    {
                        "type": "mrkdwn",
                        "text": "*Annotation* (<https://hyp.is/test_annotation_id_1/example.com/|in-context link>):",
                    },
                    {"type": "plain_text", "text": "(None)"},
                    {"type": "plain_text", "text": "test_user_1 reply"},
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "These annotations are posted to Slack by a <https://github.com/hypothesis/slack-annotations/|GitHub Actions workflow>",
                    }
                ],
            },
        ],
    }


@pytest.fixture
def search_annotations():
    return {
        "rows": [
            {
                "created": "2024-12-02T18:34:42.333087+00:00",
                "user": "acct:test_user_1@hypothes.is",
                "uri": "https://example.com/",
                "text": "test_user_1 reply",
                "document": {"title": ["Annotating the law | Hypothes.is"]},
                "links": {
                    "incontext": "https://hyp.is/test_annotation_id_1/example.com/"
                },
                "user_info": {"display_name": "md............................"},
            },
        ]
    }
