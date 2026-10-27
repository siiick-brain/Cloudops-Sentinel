# NodeCpuHigh

## Symptoms and impact

Node CPU use is above 90 percent. Request latency or container scheduling may degrade.

## Dashboards and queries

Review the node and container dashboard and query CPU idle time from node-exporter.

## Diagnosis

Identify busy containers and compare load with the active chaos scenario.

## Mitigation

Stop the stress process or reduce the source of load. Confirm CPU use falls below the threshold.

## Escalation

Escalate if the host remains saturated after the stressor stops.

