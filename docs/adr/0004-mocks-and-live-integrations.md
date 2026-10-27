# ADR 0004: Mocks in CI and manual live integrations

## Context

CI must exercise alert delivery without depending on external Slack or Jira accounts. Operators also need a configuration path for live systems.

## Decision

Use local Slack and Jira mocks by default and in CI. Mock mode always uses the local receiver URLs. Select live integrations only with explicit environment configuration. Keep credentials in the ignored `.env` file or in GitHub secrets.

## Consequences

Tests can verify deduplication, comments, transitions, retries and rate limits against local receivers. Mock contract tests do not certify remote service behavior. Live Slack and Jira verification must be performed separately.

## Rejected alternatives

- Live credentials in CI were not selected because CI is configured to run with mocks.
- Treating successful mock requests as live verification was not selected because the mocks do not contact external services.
