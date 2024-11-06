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
        display_name = annotation["user_info"]["display_name"]
        username = annotation["user"].split(":")[1].split("@")[0]
        uri = annotation["uri"]

        try:
            title = annotation["document"]["title"][0]
        except:
            title = None

        if title:
            summary = (f'{display_name} (`{username}`) annotated {uri} ("{title}"):',)
        else:
            summary = (f"{display_name} (`{username}`) annotated {uri}:",)

        block = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary},
            "fields": [
                {"type": "plain_text", "text": f"*{annotation['text']}*"},
            ],
        }

        if annotation["tags"]:
            block["fields"].append(
                {
                    "type": "mrkdwn",
                    "text": ",".join(f"`{tag}`" for tag in annotation["tags"]),
                },
            )

        return block

    if annotations:
        if len(annotations) == 1:
            summary = "A new annotation was posted"
        else:
            summary = f"{len(annotations)} new annotations were psoted"

        blocks = []

        for annotation in annotations:
            blocks.append(format_annotation(annotation))
            blocks.append({"type": "divider"})

        return json.dumps({"text": summary, "blocks": blocks})

    return ""
