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
   the search params to use (if they contain secret values like group IDs),
   and the Dead Man's Snitch IDs to report to.

6. There's a `keepalive.yml` workflow that prevents the scheduled workflows
   from getting disabled by GitHub due to repo inactivity.

## Adding another workflow

If you want to post annotations from a new search query into a new Slack channel you should:

1. Add the "GitHub Actions" Slack bot to the Slack channel that you want the workflow to post to.

2. Create a new snitch for the workflow in Dead Man's Snitch
   and put the snitch ID in a repo-level Actions secret named `YOUR_WORKFLOW_SNITCH_ID`.

   Be sure to give the snitch a good name and notes because these appear in any
   alerts sent by the snitch. See [the snitch for `eng_annotations.yml`](https://deadmanssnitch.com/snitches/a772d30828/edit)
   for an example.

   Set the snitch's alert type to "Smart".

3. Put the search query params that you want to use in a repo-level Actions variable or secret named `YOUR_WORKFLOW_SEARCH_PARAMS`.

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

4. Create a new caller workflow by copy-pasting and editing one of the existing ones,
   like [eng_annotations.yml](.github/workflows/eng_annotations.yml).

5. Add the name of your workflow to the `__scheduled_workflows` setting in [.cookiecutter/cookiecutter.json]()
   and `workflows` setting in [.github/workflows/keepalive.yml]().
