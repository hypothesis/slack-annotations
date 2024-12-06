import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from freezegun import freeze_time

from slack_annotations.core import (
    MAX_TEXT_LENGTH,
    NONE_TEXT,
    SEARCH_HOURS,
    _format_annotation,
    _format_annotations,
    _get_quote,
    _get_search_after,
    _get_text,
    _trim_text,
    notify,
)


def test_get_search_after_without_cache():
    default = "2024-12-01T00:00:00+00:00"

    assert _get_search_after("", default) == default


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


@freeze_time("2024-12-01T01:00:00+00:00")
def test_notify_with_token(search_annotations, slack_annotations, httpx_mock):
    search_after = (datetime.now(UTC) - timedelta(hours=SEARCH_HOURS)).isoformat()
    params = {
        "sort": "created",
        "order": "asc",
        "search_after": search_after,
    }
    token = "test-token"
    httpx_mock.add_response(
        url=httpx.URL("https://hypothes.is/api/search", params=params),
        content=json.dumps(search_annotations),
        match_headers={"Authorization": f"Bearer {token}"},
    )

    assert notify(token=token) == json.dumps(slack_annotations)


def test_get_quote_without_exact():
    annotation = {"target": [{"selector": []}]}

    with pytest.raises(ValueError):
        _get_quote(annotation)


def test_get_quote_with_empty_exact():
    annotation = {"target": [{"selector": [{"exact": ""}]}]}

    assert _get_quote(annotation) == NONE_TEXT


def test_trim_long_text():
    text = "a" * (MAX_TEXT_LENGTH + 1)
    stub = "..."

    assert len(_trim_text(text)) == MAX_TEXT_LENGTH
    assert _trim_text(text).endswith(stub)


def test_get_tex_with_empty_text():
    assert _get_text({}) == NONE_TEXT


def test_format_empty_annotations():
    assert _format_annotations([]) == ""


def test_format_annotation_without_title():
    annotation = {
        "user": "acct:test_user_1@hypothes.is",
        "uri": "https://example.com/",
        "links": {"incontext": "https://hyp.is/test_annotation_id_1/example.com/"},
        "user_info": {"display_name": "md............................"},
    }

    assert _format_annotation(annotation) == {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "`test_user_1` (md............................) annotated https://example.com/:",
        },
        "fields": [
            {"type": "mrkdwn", "text": "*Quote:*"},
            {
                "type": "mrkdwn",
                "text": "*Annotation* (<https://hyp.is/test_annotation_id_1/example.com/|in-context link>):",
            },
            {"type": "plain_text", "text": "(None)"},
            {"type": "plain_text", "text": "(None)"},
        ],
    }


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
