# Roadmap

## Planned

- Capture the remaining screenshots (Slack, Jira, CI and runbook views).
- Keep the router's ticket cap and Done-transition cache in Redis or Jira itself so they survive restarts and allow more than one replica.
- Send Slack messages with a bot token and `chat.postMessage` to get a real message `ts` and thread the resolved message under the firing one.
- Replace the disk-fill textfile metric with cAdvisor per-container filesystem metrics once cAdvisor supports the Docker Desktop containerd image store.
- Add a Grafana panel for `jira_ticket_creation_rejected_total`.
