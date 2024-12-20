import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from freezegun import freeze_time

from slack_annotations.core import (
    SEARCH_HOURS,
    _get_search_after,
    _make_search_params,
    notify,
)


class TestGetSearchAfter:
    @freeze_time("2024-12-01T01:00:00+00:00")
    def test_without_cache(self):
        # If there's no cached search_after time it returns one hour before now.
        assert _get_search_after() == "2024-12-01T00:00:00+00:00"

    @freeze_time("2024-12-01T01:00:00+00:00")
    def test_when_cache_file_doesnt_exist(self):
        assert _get_search_after("fake_cache.json") == "2024-12-01T00:00:00+00:00"

    @freeze_time("2024-12-01T01:00:00+00:00")
    def test_with_cache(self, tmp_path):
        cache_path = tmp_path / "cache.json"
        search_after = "2024-12-01T00:30:00+00:00"
        cache_path.write_text(json.dumps({"search_after": search_after}))

        assert _get_search_after(str(cache_path)) == search_after


class TestNotify:
    @freeze_time("2024-12-01T01:00:00+00:00")
    def test_default(self, search_annotations, slack_annotations, httpx_mock):
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

        assert notify() == slack_annotations

    @freeze_time("2024-12-01T01:00:00+00:00")
    def test_with_search_after_from_cache_file(
        self, search_annotations, slack_annotations, httpx_mock, tmp_path
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

        assert notify(cache_path=str(cache_path)) == slack_annotations
        assert json.loads(cache_path.read_text()) == {
            "search_after": "2024-12-03T18:40:42.325652+00:00"
        }

    @freeze_time("2024-12-01T01:00:00+00:00")
    def test_with_token(self, search_annotations, slack_annotations, httpx_mock):
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

        assert notify(token=token) == slack_annotations


@freeze_time("2024-12-01T01:00:00+00:00")
def test_make_search_params():
    limit = 10
    params = {"limit": limit}
    assert _make_search_params(params) == {
        "sort": "created",
        "order": "asc",
        "search_after": "2024-12-01T00:00:00+00:00",
        "limit": limit,
    }


@pytest.fixture
def slack_annotations():
    return {
        "text": "2 new annotations",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "`test_user_1` (md............................) annotated <https://example.com/|Annotating the law | Hypothes.is>:",
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Page Note* (<https://hyp.is/test_annotation_id_1/example.com/|in-context link>):",
                    },
                    {"type": "plain_text", "text": "test_user_1 reply"},
                ],
            },
            {"type": "divider"},
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
