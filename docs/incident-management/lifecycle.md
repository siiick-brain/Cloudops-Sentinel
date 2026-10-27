# Incident lifecycle

```mermaid
stateDiagram-v2
  [*] --> Detected: Alert or report
  Detected --> Triaged: Confirm signal and impact
  Triaged --> Responding: Assign incident roles
  Responding --> Mitigating: Apply a reversible mitigation
  Mitigating --> Monitoring: Confirm recovery signals
  Monitoring --> Responding: Symptoms return
  Monitoring --> Resolved: Service stable
  Resolved --> Reviewed: Record timeline and follow-up
  Reviewed --> [*]
```

Use the [severity matrix](severity-matrix.md) to set response priority. Assign an incident commander, communications lead and operations lead. Use the [communication templates](communication-templates.md) during response and the [postmortem template](postmortem-template.md) after resolution.
