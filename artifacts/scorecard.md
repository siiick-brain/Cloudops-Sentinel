# Verification scorecard

Date: 2026-10-28

| Area | Status | Evidence or blocker |
|---|---|---|
| Unit tests | Passed | 20 tests and 83.92 percent coverage on 2026-10-28 |
| Ruff | Passed | `ruff check .` ran on 2026-10-28 |
| Mypy | Passed | `mypy` ran on 2026-10-28 |
| YAML lint | Passed with warning | Repository lint returned success on 2026-10-28. It reported one blank-line warning in `monitoring/prometheus/prometheus.yml` |
| Style check | Passed | `scripts/check-style.ps1` ran on 2026-10-28 |
| README image links | Passed | `scripts/check-readme-images.ps1` passed with no broken links. A temporary missing-image link correctly made it fail |
| Relative documentation links | Passed | Relative links resolved in 45 Markdown files on 2026-10-28 |
| Compose configuration | Passed | Development and production-style Compose configuration checks ran on 2026-10-28 |
| Prometheus and Alertmanager rules | Passed in recorded run | `promtool` and `amtool` checks ran on 2026-10-27. Fresh checkout rerun remains pending |
| Local deployment verification | Passed | 25 checks on 2026-10-27; results are in `docs/deployment-verification.md` |
| Docker storage driver | Confirmed | `docker info` returned `overlayfs` and `io.containerd.snapshotter.v1` on 2026-10-28 |
| cAdvisor container metrics | Passed locally | Version 0.60.6 returned named API CPU and memory samples with the existing mounts |
| CPU, memory and disk alert scenarios | Not verified | Recorded scenarios failed to confirm their expected alerts |
| Latency, error, backend-down and network-delay scenarios | Passed in recorded runs | 2026-10-27 results are summarized in README. Local result files are ignored |
| Live Slack and Jira | Partially verified | Successful Jira requests and Slack HTTP 200 responses on 2026-10-27. Complete end-to-end live evidence is unavailable |
| Workflow execution | Not verified | CI is configured. No workflow run is recorded |
| Fresh clone README verification | Not verified | Run after committing the documentation update |
| Current branch secret scan | Passed | Gitleaks scanned all three current branch commits on 2026-10-28 and found no leaks |
| Staged change secret scan | Passed | Gitleaks scanned the pending fix commit diff on 2026-10-28 and found no leaks |
| Full workspace secret scan | Not passed | The 2026-10-28 scan found six patterns in ignored local `.env` and generated Python environment files. Values were redacted |
| All local refs secret scan | Not passed | The 2026-10-28 scan found one historical Atlassian token pattern in `.env.example` at commit `a0ef1450ee663785ecb472335147c6eb361b6667`. Do not rewrite history |
| All local refs text check | Not passed | Older local-only commit subjects contain prohibited session labels. The current branch commit subjects are clean. Do not rewrite history |
| Image captures | Planned | No screenshot files or demo GIF are present |
| Publish readiness | Not verified | Review the private publish checklist before publishing |
