from subprocess import run


def test_help():
    """Test the slack-annotations --help command."""
    run(["slack-annotations", "--help"], check=True)


def test_version():
    """Test the slack-annotations --version command."""
    run(["slack-annotations", "--version"], check=True)
