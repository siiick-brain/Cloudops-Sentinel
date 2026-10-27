# ApiAvailabilityBurnCritical

## Symptoms and impact

The API availability error budget is burning faster than the critical multi-window threshold. Users may see failed orders.

## Dashboards and queries

Open the SLO dashboard and review `api:slo_availability:ratio_rate5m` and `api:slo_error_budget:remaining_ratio`.

## Diagnosis

Check API 5xx responses, inventory readiness, recent changes and request traces in Tempo.

## Mitigation

Stop risky changes, restore dependencies and disable a confirmed fault injection. Verify successful requests before closing.

## Escalation

Page the primary on-call and assign an incident commander. Follow the [severity matrix](../incident-management/severity-matrix.md).

