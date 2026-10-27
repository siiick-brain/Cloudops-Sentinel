# TargetDown

## Symptoms and impact

A Prometheus target is not responding. The service or monitoring data may be unavailable.

## Dashboards and queries

Open Prometheus Targets and query `up == 0`.

## Diagnosis

Check the target container health, logs, network and readiness endpoint.

## Mitigation

Restore the service or correct the scrape configuration. Confirm the target returns to `up == 1`.

## Escalation

Page the on-call when the API, inventory or monitoring target remains down.

