import json

import httpx


def notify(group=None, token=None, cache_path=None):
    params = {"limit": 200, "sort": "created", "order": "asc"}

    if group:
        params["group"] = group

    if cache_path:
        print("Did receive cache_path argument")
        try:
            with open(cache_path, "r") as cache_file:
                params["search_after"] = json.load(cache_file)["search_after"]
        except FileNotFoundError:
            print("FileNotFoundError")

    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(params)
    annotations = (
        httpx.get("https://hypothes.is/api/search", params=params, headers=headers)
        .raise_for_status()
        .json()["rows"]
    )

    def format_annotation(annotation):
        return f"{annotation['user_info']['display_name']}: {annotation['text']}"

    if annotations and cache_path:
        with open(cache_path, "w") as cache_file:
            json.dump({"search_after": annotations[-1]["created"]}, cache_file)

    return "\n".join(format_annotation(annotation) for annotation in annotations)
