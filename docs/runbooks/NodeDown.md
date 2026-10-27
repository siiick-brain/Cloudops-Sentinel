# NodeDown

## Symptoms and impact

The node-exporter target is unavailable. Host metrics cannot be evaluated and dependent service alerts may be inhibited.

## Dashboards and queries

Open the node dashboard and inspect `up{job="node-exporter"}`.

## Diagnosis

Check the node-exporter container, host mount permissions and Docker Desktop Linux VM state.

## Mitigation

Restore node-exporter or the host metrics endpoint. Confirm `up` returns to one.

## Escalation

Escalate to the platform owner if the host is unavailable or dependent services remain unhealthy.

