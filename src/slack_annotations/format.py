import html
from typing import Any

MAX_TEXT_LENGTH = 2000
NONE_TEXT = "(None)"


def normalize_title(text: str) -> str:
    text = html.escape(text)
    return " ".join(text.split())


def _format_annotation(
    annotation: dict[str, Any], group_name: str | None = None
) -> dict[str, Any]:
    summary = _build_annotation_summary(annotation, group_name)
    fields = _build_annotation_fields(annotation)
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
    text = annotation.get("text")
    if not text:
        text = NONE_TEXT
    return _trim_text(text)


def format_annotations(
    annotations: list[dict[str, Any]], group_name: str | None = None
) -> dict[str, Any]:
    if not annotations:
        return {}

    summary = (
        f"{len(annotations)} new annotations"
        if len(annotations) > 1
        else "A new annotation was posted"
    )
    blocks = []
    for annotation in annotations:
        blocks.append(_format_annotation(annotation, group_name))
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

    return {"text": summary, "blocks": blocks}


def _build_annotation_summary(
    annotation: dict[str, Any], group_name: str | None = None
) -> str:
    username = html.escape(annotation["user"].split(":")[1].split("@")[0])
    display_name = html.escape(annotation["user_info"]["display_name"] or "")
    uri = annotation["uri"]

    try:
        title = normalize_title(annotation["document"]["title"][0])
    except Exception:  # pylint:disable=broad-exception-caught
        title = None
    if title:
        document_link = f"<{uri}|{title}>"
    else:
        document_link = uri

    formatted_user = (
        f"`{username}` ({display_name})" if display_name else f"`{username}`"
    )
    formatted_group = f" in `{group_name}`" if group_name else ""
    return f"{formatted_user} annotated {document_link}{formatted_group}:"


def _build_annotation_fields(annotation: dict[str, Any]) -> list[dict[str, Any]]:
    quote = None
    try:
        quote = _get_quote(annotation)
    except Exception:  # pylint:disable=broad-exception-caught
        pass
    incontext_link = annotation["links"]["incontext"]

    if quote:
        fields = [
            {"type": "mrkdwn", "text": "*Quote:*"},
            {
                "type": "mrkdwn",
                "text": f"*Annotation* (<{incontext_link}|in-context link>):",
            },
            {"type": "plain_text", "text": quote},
        ]
    elif annotation.get("references"):
        fields = [
            {
                "type": "mrkdwn",
                "text": f"*Reply* (<{incontext_link}|in-context link>):",
            },
        ]
    else:
        fields = [
            {
                "type": "mrkdwn",
                "text": f"*Page Note* (<{incontext_link}|in-context link>):",
            },
        ]
    fields.append({"type": "plain_text", "text": _get_text(annotation)})
    return fields
