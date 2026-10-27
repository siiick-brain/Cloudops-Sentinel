# ApiLatencyBurnWarning

## Symptoms and impact

The 300 ms latency objective is consuming its budget. Orders may complete slowly.

## Dashboards and queries

Open the SLO dashboard and inspect the latency objective ratio and API p95 latency.

## Diagnosis

Compare API and inventory spans, request volume and recent changes.

## Mitigation

Remove confirmed latency injection, restore the dependency path and verify p95 recovery.

## Escalation

Notify the service owner when latency burn continues for the configured windows.

