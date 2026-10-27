# ChaosContainerCpuHigh

## Symptoms and impact

The bounded chaos container is using more than half a CPU core. The host may show increased load.

## Dashboards and queries

Review the node and container dashboard and query `container_cpu_usage_seconds_total` for the chaos container.

## Diagnosis

Confirm the CPU stress scenario is active and inspect the container resource limit.

## Mitigation

Stop the stress process and verify the container CPU rate returns below the threshold.

## Escalation

Escalate if unrelated services remain saturated after the stress process stops.
