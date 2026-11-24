# ApiLatencyBurnCritical

## Symptoms and impact

More than 72 percent of API requests are slower than 300 ms over both the last 5 minutes and the last hour. At this rate (14.4 times the budget) the 30-day latency budget is gone in about two days. Most orders feel slow to users.

## Dashboards and queries

- SLO and error budget dashboard: latency objective ratio and remaining latency budget.
- Golden signals dashboard: API p95 latency. Follow an exemplar on the latency panel to a trace in Tempo.
- `api:slo_latency:ratio_rate5m` shows the share of fast requests right now.

## Diagnosis

1. Open a slow trace and compare the API span with the inventory span. A long inventory span points at the dependency or Toxiproxy; a long API span with a short inventory span points at the API itself.
2. Check for active fault injection: `GET /chaos` on the API and `GET http://localhost:8474/proxies/inventory/toxics`.
3. Check request volume and container CPU for saturation.

## Mitigation

Remove confirmed injection (`DELETE /chaos`, delete the Toxiproxy toxic), roll back a recent change or scale the slow component. Confirm that p95 falls under 300 ms and the 5-minute ratio recovers.

## Escalation

Page the service owner immediately. If the budget policy in [the SLO document](../slo.md) is breached, freeze feature releases until the budget recovers.
