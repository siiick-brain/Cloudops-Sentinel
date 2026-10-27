# ADR 0002: Dashboards as code

## Context

Dashboards must be reproducible and CI must detect changes that are not reflected in the generated files.

## Decision

Generate Grafana dashboard JSON from Python using the Grafana Foundation SDK. Provision the generated dashboards in Grafana and check generator drift in CI.

## Consequences

Dashboard definitions can be reviewed and regenerated with the project scripts. Generated JSON is checked into the repository. Manual edits to provisioned JSON can be overwritten by generation.

## Rejected alternatives

- Editing only in the Grafana UI was not selected because those changes would not be represented by the generator inputs.
- Handwritten JSON as the source was not selected because Python definitions are already the configured generation path.
