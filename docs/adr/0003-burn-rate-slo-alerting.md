# ADR 0003: Burn-rate SLO alerting

## Context

The API has availability and latency objectives over a rolling 30-day window. Operators need alerts for rapid and sustained budget consumption.

## Decision

Keep the SLO targets in the repository spec and generate Prometheus recording rules. Use multi-window burn-rate alerts for availability and latency.

## Consequences

The SLO calculations and alert expressions are versioned and tested with `promtool`. The full rolling values need 30 days of retained request data. Short local runs do not establish a contractual SLO.

## Rejected alternatives

- A single-window alert was not selected because it would not require the configured short and long windows to agree.
- A remote SLO service was not selected because the project runs locally.
