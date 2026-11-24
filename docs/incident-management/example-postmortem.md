# Exercise postmortem: injected API latency

Status: Exercise, not a production incident. Run on 2026-11-24 against real Jira Cloud and Slack. Times are measured; see [the live verification record](../live-verification.md).

Severity: SEV3 by the [severity matrix](severity-matrix.md) (degraded latency, no data loss, exercise scope).

## Summary

The latency chaos scenario added 600 ms to every API request. `ApiHighLatency` fired 80 s later. Jira issue SCRUM-10 and the Slack firing message arrived 199 s after injection. After the fault was removed the alert resolved, the router commented on the issue, moved it to Done and posted the resolved message. The exercise also exposed a timing gap in the chaos runner, which is now fixed.

## Timeline (UTC)

| Time | Event |
|---|---|
| 12:33:27 | Latency injected through the authenticated `/chaos` endpoint |
| 12:34:47 | `ApiHighLatency` active in Alertmanager (detection, 80 s) |
| 12:36:18 | Runner stops waiting for integrations and removes the fault |
| 12:36:46 | Jira issue SCRUM-10 created; Slack firing message accepted (notification, 199 s) |
| 12:42:44 | Alert resolved; resolution comment added |
| 12:42:46 | SCRUM-10 moved to Done; Slack resolved message accepted (recovery confirmed) |

## Impact

Exercise only. During the 3 minutes of injection every order request took about 600 ms longer and API p95 rose to roughly 0.9 s, against a 300 ms objective. The latency SLO burn-rate alerts did not fire because the burn lasted minutes, below their 5-minute and 30-minute windows.

## What went well

- Detection took 80 s, inside the 30 s `for` duration plus the 5-minute rate window.
- One issue was opened for the alert group and closed automatically on resolve, with the resolution time in a comment.
- The Slack message carried the value, the runbook link and the Jira link.

## What went wrong

- The runner waited 90 s for the ticket. Alertmanager knew this group from an earlier exercise and sent the new firing on its next `group_interval` tick, 120 s later, so the runner reported failure although the integrations worked.
- The router had restarted just before the run, so it had no record that the group's earlier notification had not resolved yet.
- Two resolved messages from earlier mock exercises reached the real Slack channel when the stack switched to real mode.

## Root cause

The runner's integration timeout was shorter than Alertmanager's `group_interval`. Notification latency for an existing group can reach `group_interval` plus `group_wait`.

## Action items

| Action | Owner | Status |
|---|---|---|
| Raise the integration wait to 180 s and test it against the Alertmanager config | Platform | Done |
| Require the last routed notification for the alert to be resolved before injecting | Platform | Done |
| Before a live run, wait for open mock alert groups to resolve so they do not post to the real channel | Operator | Done, documented in [integrations.md](../integrations.md) |
