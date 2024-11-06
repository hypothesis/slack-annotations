from argparse import ArgumentParser
from importlib.metadata import version

from slack_annotations.core import hello_world


def cli(argv=None):
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=version("slack-annotations"),
    )

    _args = parser.parse_args(argv)

    print(hello_world())
