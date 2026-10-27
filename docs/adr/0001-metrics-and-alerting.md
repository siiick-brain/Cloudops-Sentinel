# ADR 0001: Metrics and alerting stack

## Context

The project needs local service metrics, rule evaluation, notification grouping and dashboards that run with the Compose stack.

## Decision

Use Prometheus to scrape the services and evaluate Prometheus rules. Use Alertmanager to group, inhibit and route alerts to the FastAPI alert router. Use Grafana to query Prometheus and Tempo.

## Consequences

The stack runs locally and can be tested without an external monitoring account. Operators manage scrape targets and alert routes as repository configuration. The local host and Docker Engine remain a single failure domain.

## Rejected alternatives

- A remote managed monitoring service was not selected because the deployment is local-only.
- Sending Prometheus alerts directly to each integration was not selected. The router owns the Jira and Slack delivery behavior.
