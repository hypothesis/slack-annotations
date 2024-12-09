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
