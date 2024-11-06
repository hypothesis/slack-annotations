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
    parser.add_argument("--group")
    parser.add_argument("--token")
    parser.add_argument("--cache-path")

    args = parser.parse_args(argv)

    print(notify(args.group, args.token, args.cache_path))  # pragma: nocover
