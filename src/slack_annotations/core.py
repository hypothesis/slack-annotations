import json
from datetime import UTC, datetime, timedelta

import httpx

SEARCH_HOURS = 1


def notify(
    search_params=None, token=None, cache_path=None
):  # pylint:disable=too-complex,too-many-statements # pragma:no cover

    search_params = search_params or {}

    # Deliberately override any given sort or order param as these specific
    # values are needed for the algorithm below to work.
    search_params["sort"] = "created"
    search_params["order"] = "asc"
    search_params["search_after"] = (
        datetime.now(UTC) - timedelta(hours=SEARCH_HOURS)
    ).isoformat()

    if cache_path:
        try:
            with open(cache_path, "r", encoding="utf-8") as cache_file:
                search_params["search_after"] = max(
                    search_params["search_after"], json.load(cache_file)["search_after"]
                )
        except FileNotFoundError:
            pass

    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    annotations = (
        httpx.get(
            "https://hypothes.is/api/search", params=search_params, headers=headers
        )
        .raise_for_status()
        .json()["rows"]
    )

    if annotations and cache_path:
        with open(cache_path, "w", encoding="utf-8") as cache_file:
            json.dump({"search_after": annotations[-1]["created"]}, cache_file)

    def format_annotation(annotation):
        def get_quote(annotation):
            for target in annotation["target"]:
                for selector in target["selector"]:
                    if exact := selector.get("exact"):
                        if not exact:
                            exact = "(None)"
                        if len(exact) > 2000:
                            exact = exact[:1997] + "..."
                        return exact

            raise ValueError()

        def get_text(annotation):
            text = annotation.get("text", None)

            if not text:
                text = "(None)"

            if len(text) > 2000:
                text = text[:1997] + "..."
            return text

        try:
            quote = get_quote(annotation)
        except:  # pylint:disable=bare-except
            quote = "(None)"

        try:
            title = annotation["document"]["title"][0]
        except:  # pylint:disable=bare-except
            title = None

        fields = [
            {"type": "mrkdwn", "text": "*Quote:*"},
            {
                "type": "mrkdwn",
                "text": f"*Annotation* (<{annotation['links']['incontext']}|in-context link>):",
            },
            {"type": "plain_text", "text": quote},
            {"type": "plain_text", "text": get_text(annotation)},
        ]

        display_name = annotation["user_info"]["display_name"]
        username = annotation["user"].split(":")[1].split("@")[0]
        uri = annotation["uri"]

        if title:
            document_link = f"<{uri}|{title}>"
        else:
            document_link = uri

        summary = f"`{username}` ({display_name}) annotated {document_link}:"

        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary},
            "fields": fields,
        }

    if annotations:
        if len(annotations) == 1:
            summary = "A new annotation was posted"
        else:
            summary = f"{len(annotations)} new annotations"

        blocks = []

        for annotation in annotations:
            blocks.append(format_annotation(annotation))
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

    return ""
