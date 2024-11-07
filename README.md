<a href="https://github.com/hypothesis/slack-annotations/actions/workflows/ci.yml?query=branch%3Amain"><img src="https://img.shields.io/github/actions/workflow/status/hypothesis/slack-annotations/ci.yml?branch=main"></a>
<a><img src="https://img.shields.io/badge/python-3.13 | 3.12 | 3.11-success"></a>
<a href="https://github.com/hypothesis/slack-annotations/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-BSD--2--Clause-success"></a>
<a href="https://github.com/hypothesis/cookiecutters/tree/main/pypackage"><img src="https://img.shields.io/badge/cookiecutter-pypackage-success"></a>
<a href="https://black.readthedocs.io/en/stable/"><img src="https://img.shields.io/badge/code%20style-black-000000"></a>

# slack-annotations

Post annotations to Slack.

This repo periodically fetches annotations from the Hypothesis API and posts
them into Slack channels:

1. The `slack-annotations` script in this repo is a Python script that fetches
   annotations from the Hypothesis API and prints them out formatted as Slack
   posts.

   It accepts a Hypothesis developer token and arbitrary [annotation search API](https://h.readthedocs.io/en/latest/api-reference/v1/#tag/annotations/paths/~1search/get)
   params as command line arguments.

   The script caches the created time of the last-seen annotation and the next
   time it runs it'll only output annotations newer than that.

   You can install the script with pipx and run it locally,
   or clone this repo and run the development version of the script with tox,
   see instructions below.

2. A reusable GitHub Actions workflow [notify.yml](.github/workflows/notify.yml) calls the
   Python script and pipes the output to Slack's GitHub action to post it to Slack.

   This workflow isn't run directly, it only exists to be called by other workflows (see below).

   We have a [Slack bot](https://hypothes-is.slack.com/marketplace/A05SHSTMT5X-github-actions)
   that's used to authenticate the posting into Slack. The repo uses an
   organization-level GitHub Actions secret called `SLACK_BOT_TOKEN` to
   authenticate as the bot. The bot needs to be added to any channels that you
   want this repo to be able to post to.

3. Several caller workflows run periodically and call `notify.yml` to post
   certain annotations into certain channels. For example:

   * [eng_annotations.yml](.github/workflows/eng_annotations.yml) posts annotations
     from the "Hypothesis Eng" group into the `#eng-annotations` Slack channel.
   * [pr_website.yml](.github/workflows/pr_website.yml) posts annotations
     of the Hypothesis website into the `#pr-website` Slack channel.
   * [test.yml](.github/workflows/test.yml) posts public annotations
     into `#test-slack-annotations` for testing. This one actually doesn't run
     on a schedule, you have to run it manually.

4. Each scheduled workflow has a snitch in
   [Dead Man's Snitch](https://deadmanssnitch.com/)
   that it pings each time it runs successfully,
   so we'll get an alert from Dead Man's Snitch if it stops running.

5. The different workflows use various repo-level Actions secrets and variables
   for things like the Slack channel IDs to post to,
   the Hypothesis API authentication token to use,
   the search params to use,
   and the Dead Man's Snitch IDs to report to.

6. There's a `keepalive.yml` workflow that prevents the scheduled workflows
   from getting disabled by GitHub due to repo inactivity.

## Adding another workflow

If you want to post annotations from a new search query into a new Slack channel you should:

1. Add the "GitHub Actions" Slack bot to the Slack channel that you want the workflow to post to.

2. Copy-paste the Slack channel ID into an Actions variable named `YOUR_WORKFLOW_SLACK_CHANNEL_ID`.

3. Create a new snitch for the workflow in Dead Man's Snitch
   and put the snitch ID in a repo-level Actions secret named `YOUR_WORKFLOW_SNITCH_ID`.

   Be sure to give the snitch a good name and notes because these appear in any
   alerts sent by the snitch. See [the snitch for `eng_annotations.yml`](https://deadmanssnitch.com/snitches/a772d30828/edit)
   for an example.

   Set the snitch's alert type to "Smart".

4. Put the search query params that you want to use in a repo-level Actions variable or secret named `YOUR_WORKFLOW_SEARCH_PARAMS`.

   The query params should be formatted as a JSON object.
   You can use any of the params from the [annotation search API](https://h.readthedocs.io/en/latest/api-reference/v1/#tag/annotations/paths/~1search/get).
   For example to search for all annotations in a certain group:

   ```json
   {"group": "<GROUP_ID>"}
   ```

   Or to search for all annotations of a given site:

   ```json
   {"wildcard_uri": ["https://web.hypothes.is/*", "https://hypothes.is/*"]}
   ```

   If your search query contains any secret data (such as a group ID) then put it in an Actions secret rather than a variable.

5. Create a new caller workflow by copy-pasting and editing one of the existing ones,
   like [eng_annotations.yml](.github/workflows/eng_annotations.yml).

6. Add the name of your workflow to the `__scheduled_workflows` setting in [.cookiecutter/cookiecutter.json](.cookiecutter/cookiecutter.json)
   and `workflows` setting in [.github/workflows/keepalive.yml](.github/workflows/keepalive.yml).

## Installing

We recommend using [pipx](https://pypa.github.io/pipx/) to install
slack-annotations.
First [install pipx](https://pypa.github.io/pipx/#install-pipx) then run:

```terminal
pipx install git+https://github.com/hypothesis/slack-annotations.git
```

You now have slack-annotations installed! For some help run:

```
slack-annotations --help
```

## Upgrading

To upgrade to the latest version run:

```terminal
pipx upgrade slack-annotations
```

To see what version you have run:

```terminal
slack-annotations --version
```

## Uninstalling

To uninstall run:

```
pipx uninstall slack-annotations
```

## Setting up Your slack-annotations Development Environment

First you'll need to install:

* [Git](https://git-scm.com/).
  On Ubuntu: `sudo apt install git`, on macOS: `brew install git`.
* [GNU Make](https://www.gnu.org/software/make/).
  This is probably already installed, run `make --version` to check.
* [pyenv](https://github.com/pyenv/pyenv).
  Follow the instructions in pyenv's README to install it.
  The **Homebrew** method works best on macOS.
  The **Basic GitHub Checkout** method works best on Ubuntu.
  You _don't_ need to set up pyenv's shell integration ("shims"), you can
  [use pyenv without shims](https://github.com/pyenv/pyenv#using-pyenv-without-shims).

Then to set up your development environment:

```terminal
git clone https://github.com/hypothesis/slack-annotations.git
cd slack-annotations
make help
```

## Changing the Project's Python Versions

To change what versions of Python the project uses:

1. Change the Python versions in the
   [cookiecutter.json](.cookiecutter/cookiecutter.json) file. For example:

   ```json
   "python_versions": "3.10.4, 3.9.12",
   ```

2. Re-run the cookiecutter template:

   ```terminal
   make template
   ```

3. Commit everything to git and send a pull request

## Changing the Project's Python Dependencies

To change the production dependencies in the `setup.cfg` file:

1. Change the dependencies in the [`.cookiecutter/includes/setuptools/install_requires`](.cookiecutter/includes/setuptools/install_requires) file.
   If this file doesn't exist yet create it and add some dependencies to it.
   For example:

   ```
   pyramid
   sqlalchemy
   celery
   ```

2. Re-run the cookiecutter template:

   ```terminal
   make template
   ```

3. Commit everything to git and send a pull request

To change the project's formatting, linting and test dependencies:

1. Change the dependencies in the [`.cookiecutter/includes/tox/deps`](.cookiecutter/includes/tox/deps) file.
   If this file doesn't exist yet create it and add some dependencies to it.
   Use tox's [factor-conditional settings](https://tox.wiki/en/latest/config.html#factors-and-factor-conditional-settings)
   to limit which environment(s) each dependency is used in.
   For example:

   ```
   lint: flake8,
   format: autopep8,
   lint,tests: pytest-faker,
   ```

2. Re-run the cookiecutter template:

   ```terminal
   make template
   ```

3. Commit everything to git and send a pull request
