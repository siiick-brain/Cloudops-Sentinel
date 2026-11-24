# Verification scorecard

Date: 2026-11-24

| Area | Status | Evidence |
|---|---|---|
| Unit tests | Passed | 54 tests, 96 percent coverage of `app/` (alert router 99 percent) on Python 3.12 |
| Ruff and mypy (strict) | Passed | `ruff check .` and `mypy` |
| YAML lint and Compose | Passed | `yamllint`, `docker compose config` for the development and production-style files |
| Dashboard and SLO rule drift | Passed | Regenerated output matches the committed files |
| Prometheus rules | Passed | `promtool check rules` (14 SLO and 13 platform rules) and `promtool test rules` for burn rates, disk alerts and the disk-fill alert |
| Alertmanager | Passed | `amtool check-config` and the critical route test |
| Runbook coverage | Passed | A test checks every alert has severity, summary, description and a runbook link to an existing file on `master` |
| Stack health | Passed | All 14 services healthy and every Prometheus target up; cAdvisor scrapes take about 50 ms |
| Chaos scenarios | Passed | All seven passed on 2026-11-24 against the mocks; timings are in the README results table |
| Live Slack and Jira | Verified | 2026-11-24, SCRUM-10 created, commented and moved to Done; see `docs/live-verification.md` |
| Secret scans | Passed | Gitleaks on the committed tree and on full history with `--log-opts=--all` |
| Text audit | Passed | No prohibited terms in tracked files or commit messages; `scripts/check_public_terms.py` |
| Style | Passed | `scripts/check-style.ps1` |
| GitHub Actions | See the pull request | The workflow runs on every push; the README badge shows the latest `master` result |
| Screenshots | Partial | Grafana, Prometheus, Alertmanager and Tempo recaptured on 2026-11-24 during an injected fault. Slack, Jira, CI and runbook captures are listed in `docs/roadmap.md` |
