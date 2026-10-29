# Screenshot file status

See the [capture guide](../screenshots.md) for privacy requirements and setup.
Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\capture-all.ps1` to refresh captures.
Statuses reflect files present in this checkout. Terminal captures are rendered from captured command output.

| File | Status | Created by | Recapture when | Caption |
|---|---|---|---|---|
| `demo.gif` | Missing | `scripts/capture-all.ps1` | After a chaos exercise | Playwright video of the SLO dashboard during a chaos run |
| `P2-16-deployment-verification.png` | Present | `scripts/capture-all.ps1` | After deployment verification | rendered from captured command output |
| `P2-17-grafana-login.png` | Present | `scripts/capture-all.ps1` | When Grafana login changes | Grafana login page |
| `alertmanager-group.png` | Present | `scripts/capture-all.ps1` | When an alert is grouped | Alertmanager alerts page |
| `chaos-run.png` | Present | `scripts/capture-all.ps1` | After a chaos run | rendered from captured command output |
| `compose-services.png` | Present | `scripts/capture-all.ps1` | After Compose changes | rendered from captured command output |
| `demo-run.png` | Present | `scripts/capture-all.ps1` | After demo changes | rendered from captured command output |
| `gitleaks-history.png` | Present | `scripts/capture-all.ps1` | Before publishing | rendered from captured command output |
| `grafana-distributed-traces.png` | Present | `scripts/capture-all.ps1` | After tracing changes | Grafana distributed traces dashboard |
| `grafana-exemplar.png` | Missing | `scripts/capture-all.ps1` | When Prometheus has exemplars | Grafana Explore exemplar view |
| `grafana-golden-signals.png` | Present | `scripts/capture-all.ps1` | After generating traffic | Grafana golden signals dashboard |
| `grafana-node-container-health.png` | Present | `scripts/capture-all.ps1` | When metrics are available | Grafana node and container health dashboard |
| `grafana-slo-error-budget.png` | Present | `scripts/capture-all.ps1` | After a measured SLO exercise | Grafana SLO dashboard |
| `github-actions.png` | Missing | `scripts/capture-all.ps1` | After a public workflow run | GitHub Actions page |
| `github-contributors.png` | Missing | `scripts/capture-all.ps1` | After repository activity | GitHub contributors page |
| `github-repo.png` | Missing | `scripts/capture-all.ps1` | After public repository changes | GitHub repository page |
| `github-runbook.png` | Missing | `scripts/capture-all.ps1` | After runbook changes | GitHub rendered runbook |
| `jira-resolved.png` | Missing | `scripts/capture-all.ps1` | After a Jira issue is Done | Jira issue in Done state |
| `jira-ticket.png` | Missing | `scripts/capture-all.ps1` | After a mock or live issue is created | Jira alert ticket |
| `prometheus-alert-rules.png` | Present | `scripts/capture-all.ps1` | When alert rules change | Prometheus alerts page |
| `prometheus-container-cpu-metrics.png` | Present | `scripts/capture-all.ps1` | When cAdvisor metrics are available | Prometheus container CPU metrics page |
| `prometheus-cpu-alert-firing.png` | Present | `scripts/capture-all.ps1` | When the CPU alert is firing | Prometheus CPU alert page |
| `prometheus-targets-up.png` | Present | `scripts/capture-all.ps1` | After service health changes | Prometheus targets page |
| `pytest-results.png` | Present | `scripts/capture-all.ps1` | After test changes | rendered from captured command output |
| `slack-alert.png` | Missing | `scripts/capture-all.ps1` | After an alert reaches the configured channel | Slack firing alert |
| `slack-resolved.png` | Missing | `scripts/capture-all.ps1` | After the alert resolves | Slack resolved alert |
| `tempo-trace.png` | Present | `scripts/capture-all.ps1` | After trace data is available | Grafana view of a trace found through the Tempo API |
