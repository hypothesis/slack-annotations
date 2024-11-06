import json

import httpx


def notify(group=None, token=None, cache_path=None):
    params = {"limit": 200, "sort": "created", "order": "asc"}

    if group:
        params["group"] = group

    if cache_path:
        try:
            with open(cache_path, "r") as cache_file:
                params["search_after"] = json.load(cache_file)["search_after"]
        except FileNotFoundError:
            pass

    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    annotations = (
        httpx.get("https://hypothes.is/api/search", params=params, headers=headers)
        .raise_for_status()
        .json()["rows"]
    )

    if annotations and cache_path:
        with open(cache_path, "w") as cache_file:
            json.dump({"search_after": annotations[-1]["created"]}, cache_file)

    def format_annotation(annotation):
        def get_quote(annotation):
            for target in annotation["target"]:
                for selector in target["selector"]:
                    if exact := selector.get("exact"):
                        return exact

            raise ValueError()

        try:
            quote = get_quote(annotation)
        except:
            quote = " "

        try:
            title = annotation["document"]["title"][0]
        except:
            title = None

        fields = [
            {"type": "mrkdwn", "text": "*Quote"},
            {"type": "plain_text", "text": quote},
            {"type": "mrkdwn", "text": "*Annotation"},
            {"type": "plain_text", "text": annotation["text"]},
        ]

        if annotation["tags"]:
            fields.append(
                {
                    "type": "mrkdwn",
                    "text": ",".join(f"`{tag}`" for tag in annotation["tags"]),
                },
            )

        display_name = annotation["user_info"]["display_name"]
        username = annotation["user"].split(":")[1].split("@")[0]
        uri = annotation["uri"]

        if title:
            document_link = f"<{uri}|{title}>"
        else:
            document_link = uri

        summary = f"`{username}` ({display_name}) annotated {document_link} (<{annotation['links']['html']}|link to annotation>, <{annotation['links']['incontext']}|in-context link to annotation):"

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
