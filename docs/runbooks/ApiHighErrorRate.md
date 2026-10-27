# ApiHighErrorRate

## Symptoms and impact

More than 5 percent of API requests return 5xx responses. Order checks may fail.

## Dashboards and queries

Review the error rate panel and query `sum(rate(http_requests_total{service="api",status=~"5.."}[5m]))`.

## Diagnosis

Inspect API logs, inventory health and recent deployments.

## Mitigation

Clear an approved fault injection or restore the unhealthy dependency. Verify API requests return successfully.

## Escalation

Page the primary on-call if failures persist or customer impact expands.

