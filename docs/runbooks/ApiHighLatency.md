# ApiHighLatency

## Symptoms and impact

API p95 latency is above 300 ms. Order responses may be delayed.

## Dashboards and queries

Inspect the latency panel and compare API spans with inventory spans in Tempo.

## Diagnosis

Check request volume, API logs and toxiproxy state.

## Mitigation

Remove a confirmed latency toxic or API delay. Verify p95 latency returns below the threshold.

## Escalation

Notify the service owner if latency does not recover after the injection is cleared.

