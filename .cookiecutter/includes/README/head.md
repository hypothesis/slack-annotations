This repo periodically fetches annotations from the Hypothesis API and posts
them into Slack channels:

1. The `slack-annotations` script in this repo is a Python script that fetches
   annotations from the Hypothesis API and prints them out formatted as Slack
   posts.

   It accepts a Hypothesis developer token and arbitrary [annotation search API](https://h.readthedocs.io/en/latest/api-reference/v1/#tag/annotations/paths/~1search/get)
   params as command line arguments.

   You can install the script with pipx and run it locally,
   or clone this repo and run the development version of the script with tox,
   see instructions below.

2. A reusable GitHub Actions workflow [notify.yml](.github/workflows/notify.yml) calls the
   Python script and pipes the output to Slack's GitHub action to post it to Slack.

   We have a [Slack bot](https://hypothes-is.slack.com/marketplace/A05SHSTMT5X-github-actions)
   that's used to authenticate the posting into Slack. The repo uses an
   organization-level GitHub Actions secret called `SLACK_BOT_TOKEN` to
   authenticate as the bot. The bot needs to be added to any channels that you
   want this repo to be able to post to.

3. Several caller workflows run periodically and call `notify.yml` to post
   certain annotations into search channels. For example:

   * [eng_annotations.yml](.github/workflows/eng_annotations.yml) posts annotations
     from the "Hypothesis Eng" group into the `#eng-annotations` Slack channel.
   * [pr_website.yml](.github/workflows/pr_website.yml) posts annotations
     of the Hypothesis website into the `#pr-website` Slack channel.
   * [test.yml](.github/workflows/test.yml) posts public annotations
     into `#test-slack-annotations` for testing. This one actually doesn't run
     on a schedule, you have to run it manually.

   If you want to post the annotations from another search into another channel,
   copy one of these scripts and edit it. Remember that you'll need to add the
   Slack bot to the channel that you want to post to.

4. Each scheduled workflow has a (manually-created) snitch in
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
