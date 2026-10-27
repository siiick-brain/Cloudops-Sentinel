# Alerting flow

The flow uses the configured local mocks unless the environment explicitly selects live integrations.

```mermaid
sequenceDiagram
  participant P as Prometheus
  participant A as Alertmanager
  participant R as Alert router
  participant J as Jira mock or Jira Cloud
  participant S as Slack mock or webhook

  P->>A: Firing alert with labels and annotations
  A->>A: Group by alert name, service and severity
  A->>R: Authenticated firing webhook
  R->>J: Search for fingerprint label
  alt Existing Jira issue
    R->>J: Add repeat-firing comment
  else New Jira issue
    R->>J: Create Task with summary, ADF description and labels
    R->>J: Fetch Done transition
  end
  R->>S: Send severity, summary, value and action buttons
  S-->>R: Accept message
  J-->>R: Return issue identity
  R-->>A: Return processing result
  P->>A: Resolved alert
  A->>R: Authenticated resolved webhook
  R->>J: Add resolution comment
  R->>J: Transition issue to Done
  R->>S: Send resolved message
  R-->>A: Return processing result
```

Alertmanager groups by alert name, service and severity. Its configured repeat interval is four hours. The router applies the Jira creation limit and retries transient Jira errors and Slack rate limits. See [alerting.md](alerting.md) for silences and the scheduled maintenance mute.
