import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

SEARCH_HOURS = 1
MAX_TEXT_LENGTH = 2000
NONE_TEXT = "(None)"


def notify(
    search_params: dict[str, Any] | None = None,
    token: str | None = None,
    cache_path: str | None = None,
) -> str:
    search_params = _make_search_params(search_params, cache_path)
    headers = _make_headers(token)

    annotations = _fetch_annotations(search_params, headers)

    _maybe_update_cache(annotations, cache_path)
    return _format_annotations(annotations)


def _make_search_params(
    params: dict[str, Any] | None = None, cache_path: str | None = None
) -> dict[str, Any]:
    params = params or {}
    # Deliberately override any given sort or order param as these specific
    # values are needed for the algorithm below to work.
    params.update(
        {
            "sort": "created",
            "order": "asc",
            "search_after": _get_search_after(cache_path),
        }
    )
    return params


def _make_headers(token: str | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _get_search_after(cache_path: str | None = None) -> str:
    default = (datetime.now(UTC) - timedelta(hours=SEARCH_HOURS)).isoformat()
    if not cache_path:
        return default

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return max(default, json.load(f)["search_after"])
    except FileNotFoundError:
        pass
    return default


def _maybe_update_cache(
    annotations: list[dict[str, Any]], cache_path: str | None = None
) -> None:
    if not annotations or not cache_path:
        return
    search_after = annotations[-1]["created"]
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({"search_after": search_after}, f)


def _fetch_annotations(
    params: dict[str, Any], headers: dict[str, str]
) -> list[dict[str, Any]]:
    return (
        httpx.get("https://hypothes.is/api/search", params=params, headers=headers)
        .raise_for_status()
        .json()["rows"]
    )


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
            exact = selector.get("exact") or NONE_TEXT
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


def _format_annotations(annotations: list[dict[str, Any]]) -> str:
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
