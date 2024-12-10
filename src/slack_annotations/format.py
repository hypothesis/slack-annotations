import json
from typing import Any

MAX_TEXT_LENGTH = 2000
NONE_TEXT = "(None)"


def _format_annotation(annotation: dict[str, Any]) -> dict[str, Any]:
    fields = _build_annotation_fields(annotation)
    summary = _build_annotation_summary(annotation)
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": summary},
        "fields": fields,
    }


def _get_quote(annotation: dict[str, Any]) -> str:
    for target in annotation["target"]:
        for selector in target["selector"]:
            if exact := selector.get("exact"):
                return _trim_text(exact)
    raise ValueError()


def _trim_text(text: str) -> str:
    stub = "..."
    if len(text) > MAX_TEXT_LENGTH:
        return text[: MAX_TEXT_LENGTH - len(stub)] + stub
    return text


def _get_text(annotation: dict[str, Any]) -> str:
    text = annotation.get("text", None)
    if not text:
        text = NONE_TEXT
    return _trim_text(text)


def format_annotations(annotations: list[dict[str, Any]]) -> str:
    if not annotations:
        return ""

    summary = (
        f"{len(annotations)} new annotations"
        if len(annotations) > 1
        else "A new annotation was posted"
    )
    blocks = []
    for annotation in annotations:
        blocks.append(_format_annotation(annotation))
        blocks.append({"type": "divider"})
    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "These annotations are posted to Slack by a <https://github.com/hypothesis/slack-annotations/|GitHub Actions workflow>",
                },
            ],
        }
    )

    return json.dumps({"text": summary, "blocks": blocks})


def _build_annotation_summary(annotation: dict[str, Any]) -> str:
    username = annotation["user"].split(":")[1].split("@")[0]
    display_name = annotation["user_info"]["display_name"]
    uri = annotation["uri"]

    try:
        title = annotation["document"]["title"][0]
    except Exception:  # pylint:disable=broad-exception-caught
        title = None
    if title:
        document_link = f"<{uri}|{title}>"
    else:
        document_link = uri
    return f"`{username}` ({display_name}) annotated {document_link}:"


def _build_annotation_fields(annotation: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        quote = _get_quote(annotation)
    except Exception:  # pylint:disable=broad-exception-caught
        quote = NONE_TEXT

    return [
        {"type": "mrkdwn", "text": "*Quote:*"},
        {
            "type": "mrkdwn",
            "text": f"*Annotation* (<{annotation['links']['incontext']}|in-context link>):",
        },
        {"type": "plain_text", "text": quote},
        {"type": "plain_text", "text": _get_text(annotation)},
    ]