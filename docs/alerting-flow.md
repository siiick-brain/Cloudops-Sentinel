# Alerting flow

The flow uses local mocks by default. Live endpoints require explicit environment configuration.

```mermaid
sequenceDiagram
  participant P as Prometheus
  participant A as Alertmanager
  participant R as Alert router
  participant S as Slack mock or webhook
  participant J as Jira mock or site

  P->>A: Firing alert with labels and annotations
  A->>A: Group by alert name, service and severity
  A->>R: Authenticated firing webhook
  R->>J: Search for fingerprint label
  alt Issue already exists
    R->>J: Add repeat-firing comment
  else New issue
    R->>J: Create Task with summary, description and labels
    R->>J: Cache Done transition
  end
  R->>S: Send firing message with action buttons
  S-->>R: Accept message
  J-->>R: Return issue identity
  R-->>A: Return processing result
  Note over P,A: Alert resolves when its rule expression is no longer active
  P->>A: Resolved alert
  A->>R: Authenticated resolved webhook
  R->>J: Add resolution comment
  R->>J: Transition issue to Done
  R->>S: Send resolved message
  S-->>R: Accept message
  R-->>A: Return processing result
```

Alertmanager groups by alert name, service and severity. The configured repeat interval is four hours. The router applies a Jira issue creation limit and retries transient Jira errors and Slack rate limits. The router caches the Jira Done transition when it creates an issue and applies that transition when the alert resolves. See [alerting.md](alerting.md) for silences and the maintenance mute.
