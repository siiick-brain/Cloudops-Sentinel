# ApiAvailabilityBurnWarning

## Symptoms and impact

The API availability budget is burning above the warning threshold. Order failures may increase.

## Dashboards and queries

Open the SLO dashboard and inspect `api:slo_availability:ratio_rate5m`.

## Diagnosis

Review 5xx rate, traffic volume, dependency health and recent deployments.

## Mitigation

Pause risky changes and restore any unhealthy dependency. Confirm the burn rate falls below its threshold.

## Escalation

Notify the primary on-call if burn continues or remaining budget reaches zero.

