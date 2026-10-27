# ChaosContainerMemoryHigh

## Symptoms and impact

The bounded chaos container working set is above 80 MiB.

## Dashboards and queries

Review cAdvisor container memory and query `container_memory_working_set_bytes` for the chaos container.

## Diagnosis

Confirm the memory pressure scenario is active and compare use with the 256 MiB container limit.

## Mitigation

Stop the stress process and verify memory falls below the threshold.

## Escalation

Escalate if host memory pressure remains after recovery.
