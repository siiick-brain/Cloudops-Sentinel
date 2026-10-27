# Exercise postmortem: injected API latency

Status: Exercise completed on 2026-10-27 with local Slack and Jira mocks.

## Incident summary

The latency chaos scenario injected 600 ms of API latency. Prometheus raised `ApiHighLatency`, Alertmanager delivered the firing notification and the router created Jira mock issue `MOCK-4` and sent Slack mock message timestamp `7`. The scenario cleared the injection after the integrations were confirmed. No external users or live integrations were involved.

## Timeline

All event times are UTC.

| Event | Measured time |
|---|---|
| Latency injection | 2026-10-27 18:19:09.780 |
| `ApiHighLatency` alert observed | 2026-10-27 18:20:40.071, 90.29 seconds after injection |
| Jira and Slack mock delivery confirmed | 2026-10-27 18:20:58.762, 108.98 seconds after injection |
| Recovery completed | 2026-10-27 18:20:58.772 |

Evidence: [latency chaos result](../../artifacts/chaos-results/latency.json).

## Review

The alert and both mock integrations were confirmed. Alert evaluation and routing took about 109 seconds from injection. This exercise does not measure customer impact or prove live Slack and Jira delivery.

## Follow-up actions

| Action | Owner | Due date | Status |
|---|---|---|---|
| Verify alert and ticket timing with real integrations | Project operator | Before live verification | Not verified |
