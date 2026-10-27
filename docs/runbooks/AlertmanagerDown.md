# AlertmanagerDown

## Symptoms and impact

Alertmanager is unavailable. Prometheus notifications may not reach receivers.

## Dashboards and queries

Check `http://localhost:9093/-/healthy` and the Alertmanager container logs.

## Diagnosis

Review configuration validity, receiver connectivity and container health.

## Mitigation

Restore valid configuration and verify alert delivery with a controlled test.

## Escalation

Page the monitoring owner if notification delivery remains unavailable.

