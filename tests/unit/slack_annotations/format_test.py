import pytest

from slack_annotations.format import (
    MAX_TEXT_LENGTH,
    _format_annotation,
    _get_quote,
    _trim_text,
    format_annotations,
)


def test_get_quote_without_exact():
    annotation = {"target": [{"selector": []}]}

    with pytest.raises(ValueError):
        _get_quote(annotation)


def test_trim_long_text():
    text = "a" * (MAX_TEXT_LENGTH + 1)
    stub = "..."

    assert len(_trim_text(text)) == MAX_TEXT_LENGTH
    assert _trim_text(text).endswith(stub)


def test_format_empty_annotations():
    assert not format_annotations([])


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
        "text": "2 new annotations",
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
