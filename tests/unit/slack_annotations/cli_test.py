from importlib.metadata import version

import pytest

from slack_annotations.cli import cli


def test_help():
    with pytest.raises(SystemExit) as exc_info:
        cli(["--help"])

    assert not exc_info.value.code


def test_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli(["--version"])

    assert capsys.readouterr().out.strip() == version("slack-annotations")
    assert not exc_info.value.code


def test_default(capsys, mocker):
    notify = mocker.patch("slack_annotations.cli.notify")
    notify_output = "Test notify output"
    notify.return_value = notify_output

    cli([])

    notify.assert_called_once_with(None, None, None)
    assert capsys.readouterr().out.strip() == notify_output
