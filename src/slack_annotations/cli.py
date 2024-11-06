from argparse import ArgumentParser
from importlib.metadata import version


def cli(argv=None):
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=version("slack-annotations"),
    )

    _args = parser.parse_args(argv)
