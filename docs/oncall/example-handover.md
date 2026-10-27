# Exercise handover: injected API latency

Status: Exercise completed on 2026-10-27. Full live verification remains incomplete.

## Summary

The latency exercise injected 600 ms of API latency. `ApiHighLatency` fired 85.26 seconds after injection. The runner confirmed successful Jira and Slack responses at a shared polling time of 103.63 seconds after injection. Separate delivery times and a Slack timestamp were not recorded. Recovery completed at 21:46:08 UTC.

## Handover

The exercise is complete and no fault injection remains active. This was not a production incident. Before another live exercise, verify the integration configuration, confirm the maintenance window and assign an incident commander. See the [measured result](../../artifacts/chaos-results/latency.json) and [exercise postmortem](../incident-management/example-postmortem.md).
