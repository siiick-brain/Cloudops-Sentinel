# Live integration verification

Status: Verified.

Date: 2026-11-24.

The latency scenario ran against real Jira Cloud and a real Slack incoming webhook (`INTEGRATION_MODE=real`, `chaos/run.py latency --live`). Times are UTC, taken from the alert-router log and the Jira REST API.

| Step | Time | Evidence |
|---|---|---|
| Latency injected (600 ms) | 12:33:27 | Runner result |
| `ApiHighLatency` active in Alertmanager | 12:34:47 | Runner poll, 80.3 s after injection |
| Jira issue SCRUM-10 created | 12:36:46 | Jira `created` field, 199 s after injection |
| Slack firing message accepted | 12:36 | Router log `slack_message_accepted`, HTTP 200 |
| Fault removed | 12:36:18 | Runner recovery |
| Resolution comment added | 12:42:44 | Jira comment `Resolved at 2026-11-24T12:42:44Z.` |
| Issue moved to Done | 12:42:46 | Jira `resolutiondate`; transition request returned 204 |
| Slack resolved message accepted | 12:42 | Router log `slack_message_accepted`, HTTP 200 |

The issue is a Task with summary `[WARNING] ApiHighLatency` and labels `warning`, `api` and `fp-63caf2f2f14a7f5e`. The workspace URL is not stored here.

## What this run found

The runner waited 90 s for the integrations and stopped at 12:36:18. Alertmanager already knew this group from an earlier exercise, so it sent the new firing on its next `group_interval` tick (120 s) and the ticket arrived 28 s after the runner gave up. The integration wait is now 180 s, which covers `group_interval` plus `group_wait`. A unit test keeps it above the Alertmanager settings.

Slack incoming webhooks return a plain `ok` and no message `ts`. The router records the acceptance time from the `Date` header of Slack's 200 response instead.

## Repeat the run

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\live-demo.ps1
```

The script needs `INTEGRATION_MODE=real` and the Jira and Slack values in `.env`. It prints the issue URL, the Slack acceptance time and the seconds from injection to ticket. It rewrites this file. Results with real URLs go to the gitignored `artifacts/live-results/`.
