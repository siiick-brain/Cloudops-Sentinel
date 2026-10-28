# Exercise postmortem: injected API latency

Status: Exercise completed on 2026-10-27. The recorded run received successful Jira and Slack responses. Full live verification remains incomplete.

## Incident summary

The latency chaos scenario injected 600 ms of API latency. Prometheus raised `ApiHighLatency` and Alertmanager delivered the firing notification. The router returned a Jira issue URL and Slack accepted the message. The issue URL and Slack message timestamp are not recorded here. The runner cleared the injection after the integration checks completed.

## Timeline

All event times are UTC.

| Event | Measured time |
|---|---|
| Latency injection | 2026-10-27 runner result |
| `ApiHighLatency` alert observed | 85.26 seconds after injection |
| Jira and Slack responses confirmed by the same runner poll | 103.63 seconds after injection |
| Recovery completed | 2026-10-27 21:46:08 UTC |

Evidence: [recorded results in the README](../../README.md#results).

## Review

The alert and both integration checks passed. The runner recorded one shared confirmation time, not separate Slack and Jira delivery times. This exercise does not measure customer impact. The full manual live verification record remains incomplete.

## Follow-up actions

| Action | Owner | Due date | Status |
|---|---|---|---|
| Complete a live verification record with separate integration timing where available | Project operator | Before claiming full live verification | Not verified |
