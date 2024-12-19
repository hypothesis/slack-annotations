import json
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


def test_default(capsys, notify):
    notify.return_value = "Test notify output"

    cli([])

    notify.assert_called_once_with(
        search_params=None, token=None, cache_path=None, group_name=None
    )
    assert capsys.readouterr().out.strip() == json.dumps(notify.return_value)


def test_search_params(capsys, notify):
    notify.return_value = "Test notify output"

    search_params = {"some_key": "some_value"}
    cli(["--search-params", json.dumps(search_params)])

    notify.assert_called_once_with(
        search_params=search_params, token=None, cache_path=None, group_name=None
    )
    assert capsys.readouterr().out.strip() == json.dumps(notify.return_value)


@pytest.fixture(autouse=True)
def notify(mocker):
    return mocker.patch("slack_annotations.cli.notify", autospec=True)
