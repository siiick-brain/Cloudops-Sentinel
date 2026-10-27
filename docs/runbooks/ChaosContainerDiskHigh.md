# ChaosContainerDiskHigh

## Symptoms and impact

The bounded chaos container filesystem use is above 50 MiB.

## Dashboards and queries

Review cAdvisor filesystem metrics and query `container_fs_usage_bytes` for the chaos container.

## Diagnosis

Confirm the disk-fill scenario is active and verify the written file remains within its 64 MiB limit.

## Mitigation

Remove the bounded test file and stop the chaos container. Confirm filesystem use falls.

## Escalation

Escalate if the host filesystem is affected or the container does not recover.
