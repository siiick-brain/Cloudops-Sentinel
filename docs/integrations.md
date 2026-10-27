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

The router refuses to start in real mode when a required value is missing. It uses Jira REST API v3 basic authentication, searches by fingerprint label, adds a comment to repeated firings, comments on resolution and requests the Jira Done transition. Transient Jira errors and Slack 429 responses are retried. Ticket creation is capped by `JIRA_MAX_ISSUES_PER_HOUR`.

Do not paste tokens, webhook URLs or account data into source files or issue reports. Use `.env` for local work and GitHub secrets for automation. No real credentials are provided in this repository.

## Payload behavior

Slack messages include severity, summary, service and a value field with dashboard, runbook and ticket buttons. Jira issues include project, Task issue type, severity summary, description in Atlassian Document Format and labels for severity, service and fingerprint. Mocks test the local contract but do not certify the remote service schemas.
