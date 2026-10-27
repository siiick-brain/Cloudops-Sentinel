# PrometheusDown

## Symptoms and impact

Prometheus is unavailable. Metrics and alert evaluations may stop.

## Dashboards and queries

Check `http://localhost:9090/-/healthy` and the Prometheus container logs.

## Diagnosis

Review configuration validity, storage availability and recent restarts.

## Mitigation

Restore a valid configuration or available storage, then confirm Prometheus is healthy.

## Escalation

Page the monitoring owner if alert evaluation does not recover.

