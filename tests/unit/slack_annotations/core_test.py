import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from freezegun import freeze_time

from slack_annotations.core import (
    MAX_TEXT_LENGTH,
    SEARCH_HOURS,
    _fetch_annotations,
    _format_annotations,
    _get_quote,
    _get_search_after,
    _init_search_params,
    _trim_text,
    _update_cache,
    notify,
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


def test_get_search_after_without_cache():
    default = "2024-12-01T00:00:00+00:00"
    assert _get_search_after("", default) == default


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
    assert _format_annotations(search_annotations["rows"]) == json.dumps(
        slack_annotations
    )


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


@freeze_time("2024-12-01T01:00:00+00:00")
def test_notify_with_search_after_from_cache_file(
    search_annotations, slack_annotations, httpx_mock, tmp_path
):
    search_after = "2024-12-01T00:30:00+00:00"
    params = {
        "sort": "created",
        "order": "asc",
        "search_after": search_after,
    }
    httpx_mock.add_response(
        url=httpx.URL("https://hypothes.is/api/search", params=params),
        content=json.dumps(search_annotations),
    )
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"search_after": search_after}))

    assert notify(cache_path=str(cache_path)) == json.dumps(slack_annotations)
    assert json.loads(cache_path.read_text()) == {
        "search_after": "2024-12-03T18:40:42.325652+00:00"
    }


def test_get_quote_without_exact():
    annotation = {"target": [{"selector": [{}]}]}

    with pytest.raises(ValueError):
        _get_quote(annotation)


def test_trim_long_text():
    text = "a" * (MAX_TEXT_LENGTH + 1)
    stub = "..."
    assert len(_trim_text(text)) == MAX_TEXT_LENGTH
    assert _trim_text(text).endswith(stub)


@pytest.fixture
def slack_annotations():
    return {
        "text": "A new annotation was posted",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "`test_user_2` (Test User 2) annotated <https://web.hypothes.is/blog/step-by-step-guide-to-using-hypothesis-for-collaborative-projects/|Annotating the law | Hypothes.is>:",
                },
                "fields": [
                    {"type": "mrkdwn", "text": "*Quote:*"},
                    {
                        "type": "mrkdwn",
                        "text": "*Annotation* (<https://hyp.is/test_annotation_id_2/web.hypothes.is/blog/step-by-step-guide-to-using-hypothesis-for-collaborative-projects/|in-context link>):",
                    },
                    {
                        "type": "plain_text",
                        "text": "The ability to collaborate effectively is invaluable in today\u2019s interconnected world. Whether in academic or professional settings, tools that streamline communication, enhance content sharing and promote open dialogue are important. Hypothesis is a standout tool in this regard, especially renowned for its capabilities in group annotations and as an online learning tool.",
                    },
                    {"type": "plain_text", "text": "A useful tool!"},
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
                "created": "2024-12-03T18:40:42.325652+00:00",
                "user": "acct:test_user_2@hypothes.is",
                "uri": "https://web.hypothes.is/blog/step-by-step-guide-to-using-hypothesis-for-collaborative-projects/",
                "text": "A useful tool!",
                "target": [
                    {
                        "source": "https://web.hypothes.is/blog/step-by-step-guide-to-using-hypothesis-for-collaborative-projects/",
                        "selector": [
                            {
                                "exact": "The ability to collaborate effectively is invaluable in today’s interconnected world. Whether in academic or professional settings, tools that streamline communication, enhance content sharing and promote open dialogue are important. Hypothesis is a standout tool in this regard, especially renowned for its capabilities in group annotations and as an online learning tool."
                            },
                        ],
                    }
                ],
                "document": {"title": ["Annotating the law | Hypothes.is"]},
                "links": {
                    "incontext": "https://hyp.is/test_annotation_id_2/web.hypothes.is/blog/step-by-step-guide-to-using-hypothesis-for-collaborative-projects/"
                },
                "user_info": {"display_name": "Test User 2"},
            },
        ]
    }
