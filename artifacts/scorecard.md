# Verification scorecard

Date: 2026-10-29

| Area | Status | Evidence |
|---|---|---|
| Unit tests | Passed | `pytest -q`: 25 tests passed with 83.92 percent coverage on 2026-10-29 |
| Ruff | Passed | `ruff check .` passed on 2026-10-29 |
| Mypy | Passed | `mypy` passed on 2026-10-29 |
| Style check | Passed | `scripts/check-style.ps1` passed on 2026-10-29 |
| README image links | Passed | `scripts/check-readme-images.ps1` passed on 2026-10-29 |
| Compose configuration | Passed | Development and production-style `docker compose config --quiet` checks passed on 2026-10-29 |
| Prometheus and Alertmanager rules | Passed | `promtool check rules` found 13 rules in each file. Rule tests, Alertmanager config and the critical route check passed on 2026-10-29 |
| Fresh-clone verification | Not current | The fresh clone was checked before the final documentation adjustments. The exact final commit was not cloned |
| Demo script | Blocked | The 2026-10-29 run stopped before the demo or chaos check because port 8090 was already allocated. A fresh-checkout demo passed on 2026-10-28 |
| Local deployment verification | Passed in recorded run | 25 checks on 2026-10-27; results are in `docs/deployment-verification.md` |
| Docker storage driver | Confirmed in recorded run | `overlayfs` and `io.containerd.snapshotter.v1` were reported on 2026-10-28 |
| cAdvisor container metrics | Passed in recorded run | Version 0.60.6 returned named API CPU and memory samples with the existing mounts |
| Chaos scenarios | Mixed | Recorded results are listed in the README. Latency and disk-fill runs on 2026-10-29 did not confirm their expected alerts |
| Live Slack and Jira | Partially verified | The manual exercise on 2026-10-27 recorded successful Jira requests and Slack HTTP 200 responses. Complete end-to-end live evidence is unavailable |
| Workflow execution | Not verified | The workflow is configured. No workflow run is recorded |
| Selected screenshots | Present | The README links the nine selected original screenshots. Every present PNG is under 500 KB |
| Automated recapture | Not run | The selected original screenshots remain in the gallery. The demo could not start because port 8090 was already allocated |
| Demo GIF | Missing | No GIF is present in `docs/images/` |
| Working-tree secret scan | Findings | Gitleaks reported eight redacted matches in ignored `.env` and `.venv` files. Keep those local files out of commits |
| Git history secret scan | No findings reported | `gitleaks git --log-opts="--all"` returned no findings and reported 20 commits scanned. A separate redacted Gitleaks scan of the `git log --all --full-history -p` stream scanned about 1.27 MB and found no leaks across the 68 reachable commits |
| Author and message audit | Reviewed | All 68 reachable commits use the configured author identity. No `Co-authored-by` trailers were found. Older session-labeled subjects remain in history |
| Publish readiness | Not verified | See the private publish checklist for scan details and remaining commands |
