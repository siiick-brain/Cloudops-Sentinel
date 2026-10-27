# Verification scorecard

Date: 2026-10-27

| Area | Status | Evidence or blocker |
|---|---|---|
| Unit tests | Passed | 19 tests, 83.67 percent coverage |
| Ruff | Passed | `ruff check .` |
| Mypy | Passed | `mypy` |
| YAML lint | Passed | Changed Compose and workflow files pass targeted lint. Full repository lint reports an existing warning in `monitoring/prometheus/prometheus.yml` |
| Style check | Passed | `scripts/check-style.ps1` |
| Public source text | Passed | Project files contain no prohibited terms |
| Dashboard and SLO drift tests | Passed | Pytest generator checks |
| Compose syntax | Passed | `docker compose config --quiet` |
| Production Compose configuration | Passed | `docker compose -f compose.prod.yml config --quiet` |
| Local production deployment | Passed | 25 HTTPS, TLS, header, port, path and authentication checks on 2026-10-27 |
| Docker storage driver | Confirmed | Docker reports `overlayfs` and `io.containerd.snapshotter.v1` on this host |
| cAdvisor v0.49.2 metrics | Failed locally | Repeated layer-ID errors and no named per-container CPU samples |
| cAdvisor v0.60.6 candidate | Passed locally | A temporary container with the existing mounts exposed named CPU samples for project containers |
| Local deployment verification | Passed | Results are recorded in `docs/deployment-verification.md` |
| Linux CI deployment verification | Not verified | Workflow configured; no successful run is recorded |
| Project tree secret scan | Passed | Nonignored project files had no findings |
| Full workspace secret scan | Not passed | Five findings are in the ignored local `.env` and one generic-key pattern is in ignored generated Python dependency code |
| Git history secret scan | Not passed | A historical environment example contains a credential finding; rotate it if real |
| Git history text check | Not passed | Existing internal history refs fail the message check and were not rewritten |
| Prometheus rules | Passed | Pinned image `promtool check rules` passed |
| SLO alert rules | Passed | Pinned image `promtool test rules` passed |
| Alertmanager config and routes | Passed | `amtool check-config` and warning/critical route tests passed |
| Stack startup | Passed | All 14 services were running and configured health checks passed |
| End-to-end mock demo | Passed | Stack readiness, request, cross-service trace, latency alert and ticket/message verified |
| Latency chaos | Passed | Alert at 90.29 seconds, ticket and message at 108.98 seconds |
| Error chaos | Passed | Alert at 70.18 seconds, ticket and message at 88.84 seconds |
| Backend-down chaos | Passed | Alert at 80.39 seconds, ticket and message at 80.45 seconds |
| Network-delay chaos | Passed | Alert at 90.34 seconds, ticket and message at 109.11 seconds |
| Container resource alerts | Not verified | Dashboard metric availability is tested with a candidate image. Alert firing needs scenario results or a Linux CI run |
| Live Slack and Jira | Not verified | No populated `.env` is present |
| Fresh clone check | Not verified | No commit exists yet |
| CI workflow execution | Not verified | No workflow run exists |
| Screenshots | Planned | Capture them using [docs/screenshots.md](../docs/screenshots.md) |
