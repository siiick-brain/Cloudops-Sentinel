# Exercise handover: injected API latency

Shift: 2026-11-24, ending 13:00 UTC. Exercise, not a production incident.

## Status

- Active alerts: none.
- Open tickets: none. SCRUM-10 from the latency exercise is Done.
- Fault injection: none active. `/chaos` is cleared, no Toxiproxy toxics, `chaos-tools` stopped.
- Integration mode: back to mock after the live run.

## What happened

At 12:33 the latency scenario added 600 ms to API requests. `ApiHighLatency` fired after 80 s and SCRUM-10 plus the Slack message arrived after 199 s. The alert resolved at 12:42 and the router closed SCRUM-10. Details are in the [exercise postmortem](../incident-management/example-postmortem.md).

## Watch next shift

- The chaos runner integration wait was raised to 180 s. The next run of any scenario should report Slack and Jira within that window.
- Two resolved messages from earlier mock exercises reached the real Slack channel. They need no action.

