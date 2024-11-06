import httpx


def notify(group=None, token=None):
    params = {"limit": 200, "sort": "created"}

    if group:
        params["group"] = group

    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    annotations = (
        httpx.get("https://hypothes.is/api/search", params=params, headers=headers)
        .raise_for_status()
        .json()["rows"]
    )

    def format_annotation(annotation):
        return f"{annotation['user_info']['display_name']}: {annotation['text']}"

    return "\n".join(format_annotation(annotation) for annotation in annotations)
