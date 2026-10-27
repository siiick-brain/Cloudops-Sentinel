# NodeDiskFillingSoon

## Symptoms and impact

The observed filesystem growth rate predicts exhaustion within 24 hours.

## Dashboards and queries

Review filesystem available space and `predict_linear(node_filesystem_avail_bytes[6h], 24 * 3600)`.

## Diagnosis

Confirm the filesystem and assess whether the six-hour growth trend is representative.

## Mitigation

Stop unnecessary writes and plan safe cleanup or capacity changes.

## Escalation

Escalate to the platform owner if the predicted exhaustion remains after cleanup.

