# Live integration verification

Status: Not fully verified.

On 2026-10-27 the router logged successful Jira requests and Slack HTTP 200 responses. A complete live verification record is not available. The incoming webhook response did not provide a Slack message timestamp.

Use the local `.env` credentials to run `.\scripts\live-demo.ps1` or `sh scripts/live-demo.sh`. Record the Jira issue URL and injection-to-ticket duration after confirming the Jira issue and Slack message. Record the Slack timestamp only if Slack returns one.
