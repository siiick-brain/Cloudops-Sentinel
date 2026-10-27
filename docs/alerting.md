# Alert routing and maintenance

Alertmanager groups by alert name, service and severity. Critical and warning routes forward notifications to alert-router. The router delivers Slack messages and creates or updates Jira issues. CI uses local mocks.

## Create a silence

1. Open Alertmanager at `http://localhost:9093`.
2. Select the firing alert and choose to silence it.
3. Use exact matchers for alert name and service. Avoid broad matchers.
4. Enter an owner and reason in the comment.
5. Set a start time and a short expiry in UTC.
6. Confirm the preview matches only the intended alert.
7. Verify the silence appears in the active silence list and remove it after maintenance.

## Scheduled maintenance mute

The `scheduled-maintenance` interval is Sunday from 02:00 to 03:00 UTC. It applies only to alerts with the `maintenance="true"` label. The default alert rules do not set that label. Set and review it only for a planned maintenance change, then remove it when maintenance ends. The interval does not replace an expiring alert silence.
