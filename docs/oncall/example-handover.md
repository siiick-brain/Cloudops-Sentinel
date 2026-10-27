# Exercise handover: injected API latency

Status: Exercise completed on 2026-10-27 using local mocks.

## Summary

The latency exercise injected 600 ms of API latency. `ApiHighLatency` fired 90.29 seconds after injection. The alert reached Jira mock issue `MOCK-4` and Slack mock timestamp `7` 108.98 seconds after injection. The chaos runner removed the injection and completed recovery at 18:20:58.772 UTC.

## Handover

The exercise is complete and no fault injection remains active. This was a local mock run, not a production incident. Before any live exercise, verify the integration credentials, confirm the maintenance window and assign an incident commander. See the [measured result](../../artifacts/chaos-results/latency.json) and [exercise postmortem](../incident-management/example-postmortem.md).
