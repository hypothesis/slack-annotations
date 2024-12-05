import pytest

from slack_annotations.format import (
    MAX_TEXT_LENGTH,
    _format_annotation,
    _get_quote,
    _trim_text,
    format_annotations,
)


class TestGetQuote:
    def test_without_exact(self):
        annotation = {"target": [{"selector": []}]}

        with pytest.raises(ValueError):
            _get_quote(annotation)

    def test_with_exact(self):
        exact = "test_exact"
        annotation = {"target": [{"selector": [{"exact": exact}]}]}

        assert _get_quote(annotation) == exact

    def test_with_exact_multiple_selectors(self):
        exact = "test_exact"
        annotation = {"target": [{"selector": [{}, {"exact": exact}]}]}

        assert _get_quote(annotation) == exact


def test_trim_long_text():
    text = "a" * (MAX_TEXT_LENGTH + 1)
    stub = "..."

    assert len(_trim_text(text)) == MAX_TEXT_LENGTH
    assert _trim_text(text).endswith(stub)


def test_format_empty_annotations():
    assert not format_annotations([])


class TestFormatAnnotation:
    def test_without_title(self):
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

    def test_without_user_info(self):
        annotation = {
            "user": "acct:test_user_1@hypothes.is",
            "uri": "https://example.com/",
            "links": {"incontext": "https://hyp.is/test_annotation_id_1/example.com/"},
            "document": {"title": ["Annotation title"]},
            "user_info": {"display_name": None},
        }

        assert _format_annotation(annotation) == {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "`test_user_1` annotated <https://example.com/|Annotation title>:",
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
