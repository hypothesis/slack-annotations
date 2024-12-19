import json
from argparse import ArgumentParser
from importlib.metadata import version

from slack_annotations.core import notify


def cli(argv=None):
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=version("slack-annotations"),
    )
    parser.add_argument("--search-params")
    parser.add_argument("--token")
    parser.add_argument("--cache-path")
    parser.add_argument("--group-name")

    args = parser.parse_args(argv)

    if args.search_params:
        search_params = json.loads(args.search_params)
    else:
        search_params = None

    annotations = notify(
        search_params=search_params,
        token=args.token,
        cache_path=args.cache_path,
        group_name=args.group_name,
    )
    print(json.dumps(annotations) if annotations else "")
