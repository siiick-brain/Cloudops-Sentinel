# Integrations

The default stack routes Alertmanager notifications to the local alert-router. The router sends Block Kit shaped messages to mock Slack and creates or updates issues in mock Jira.

## Local defaults

The mocks are selected with `INTEGRATION_MODE=mock`. They expose local ports 8091 and 8092. The state is in memory and resets when a mock restarts.

Mock mode forces the router to use the local receiver addresses even when `.env` contains real Jira or Slack endpoint values.

## Real Slack and Jira

1. Copy `.env.example` to `.env`.
2. Set `INTEGRATION_MODE=real`.
3. Set `JIRA_BASE_URL` to the Jira Cloud site URL.
4. Set `JIRA_EMAIL`, `JIRA_API_TOKEN` and `JIRA_PROJECT_KEY`.
5. Set `SLACK_WEBHOOK_URL` to the Slack incoming webhook.
6. Set unique `ROUTER_SHARED_TOKEN` and `CHAOS_TOKEN` values.
7. Start the stack and confirm that alert-router becomes healthy.
8. Run `.\scripts\live-demo.ps1` or `sh scripts/live-demo.sh` to exercise one scenario.

The router refuses to start in real mode when a required value is missing (`ROUTER_SHARED_TOKEN` included) and names the missing variable. It uses Jira REST API v3 basic authentication.

Alertmanager sends one webhook per group (alert name, service and severity). The router hashes the group key into a fingerprint label, so a group of three alerts gets one issue. The description says how many alerts are in the group.

Before it creates an issue the router searches with JQL for that label among issues that are not Done. A repeat firing adds a comment. If the group fires again after its issue is Done, it gets a new issue.

When the group resolves, the router comments with the resolution time and moves the issue to Done. It reads the Done transition ID from the Jira API at start-up and looks it up again if an issue uses another workflow.

Jira 5xx, 429 and network errors are retried with backoff (1, 2 and 4 s). On a Slack 429 the router waits for the `Retry-After` delay Slack sends, up to 30 s.

`JIRA_MAX_ISSUES_PER_HOUR` caps new issues per hour. A rejected creation increments `jira_ticket_creation_rejected_total`, still goes to Slack and gets a 200 back to Alertmanager so it is not retried. The counter is in memory and resets when the router restarts, which is fine for one replica.

Do not paste tokens, webhook URLs or account data into source files or issue reports. Use `.env` for local work and GitHub secrets for automation. No real credentials are provided in this repository.

## Payload behavior

Slack messages include severity, summary, service and a value field with dashboard, runbook and ticket buttons. Jira issues include project, Task issue type, severity summary, description in Atlassian Document Format and labels for severity, service and fingerprint. Mocks test the local contract but do not certify the remote service schemas.

Slack incoming webhooks answer a plain `ok` and never return a message `ts`. The router therefore records when Slack accepted the message, taken from the `Date` header of its 200 response and reports that as the Slack timestamp.

## Choosing mock or real

`scripts/demo.ps1`, `scripts/demo.sh` and `chaos/run.py` always use the mocks, whatever `.env` says. `chaos/run.py --live` and `scripts/live-demo.ps1` use real Slack and Jira. The runner reads the router's mode from `/healthz` and stops with a clear message when the two disagree.

Before a live run, let open mock alert groups resolve (Alertmanager shows no active alerts) so their resolved notifications do not reach the real Slack channel when the router switches to real mode.
