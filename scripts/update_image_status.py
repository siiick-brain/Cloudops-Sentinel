from __future__ import annotations

from capture_support import ROOT

IMAGES: list[tuple[str, str, str, str]] = [
    (
        "demo.gif",
        "scripts/capture-all.ps1",
        "After a chaos exercise",
        "Playwright video of the SLO dashboard during a chaos run",
    ),
    (
        "P2-16-deployment-verification.png",
        "scripts/capture-all.ps1",
        "After deployment verification",
        "rendered from captured command output",
    ),
    (
        "P2-17-grafana-login.png",
        "scripts/capture-all.ps1",
        "When Grafana login changes",
        "Grafana login page",
    ),
    (
        "alertmanager-group.png",
        "scripts/capture-all.ps1",
        "When an alert is grouped",
        "Alertmanager alerts page",
    ),
    (
        "chaos-run.png",
        "scripts/capture-all.ps1",
        "After a chaos run",
        "rendered from captured command output",
    ),
    (
        "compose-services.png",
        "scripts/capture-all.ps1",
        "After Compose changes",
        "rendered from captured command output",
    ),
    (
        "demo-run.png",
        "scripts/capture-all.ps1",
        "After demo changes",
        "rendered from captured command output",
    ),
    (
        "gitleaks-history.png",
        "scripts/capture-all.ps1",
        "Before publishing",
        "rendered from captured command output",
    ),
    (
        "grafana-distributed-traces.png",
        "scripts/capture-all.ps1",
        "After tracing changes",
        "Grafana distributed traces dashboard",
    ),
    (
        "grafana-exemplar.png",
        "scripts/capture-all.ps1",
        "When Prometheus has exemplars",
        "Grafana Explore exemplar view",
    ),
    (
        "grafana-golden-signals.png",
        "scripts/capture-all.ps1",
        "After generating traffic",
        "Grafana golden signals dashboard",
    ),
    (
        "grafana-node-container-health.png",
        "scripts/capture-all.ps1",
        "When metrics are available",
        "Grafana node and container health dashboard",
    ),
    (
        "grafana-slo-error-budget.png",
        "scripts/capture-all.ps1",
        "After a measured SLO exercise",
        "Grafana SLO dashboard",
    ),
    (
        "github-actions.png",
        "scripts/capture-all.ps1",
        "After a public workflow run",
        "GitHub Actions page",
    ),
    (
        "github-contributors.png",
        "scripts/capture-all.ps1",
        "After repository activity",
        "GitHub contributors page",
    ),
    (
        "github-repo.png",
        "scripts/capture-all.ps1",
        "After public repository changes",
        "GitHub repository page",
    ),
    (
        "github-runbook.png",
        "scripts/capture-all.ps1",
        "After runbook changes",
        "GitHub rendered runbook",
    ),
    (
        "jira-resolved.png",
        "scripts/capture-all.ps1",
        "After a Jira issue is Done",
        "Jira issue in Done state",
    ),
    (
        "jira-ticket.png",
        "scripts/capture-all.ps1",
        "After a mock or live issue is created",
        "Jira alert ticket",
    ),
    (
        "prometheus-alert-rules.png",
        "scripts/capture-all.ps1",
        "When alert rules change",
        "Prometheus alerts page",
    ),
    (
        "prometheus-container-cpu-metrics.png",
        "scripts/capture-all.ps1",
        "When cAdvisor metrics are available",
        "Prometheus container CPU metrics page",
    ),
    (
        "prometheus-cpu-alert-firing.png",
        "scripts/capture-all.ps1",
        "When a disk alert is firing",
        "Prometheus NodeDiskHigh alert page",
    ),
    (
        "prometheus-targets-up.png",
        "scripts/capture-all.ps1",
        "After service health changes",
        "Prometheus targets page",
    ),
    (
        "pytest-results.png",
        "scripts/capture-all.ps1",
        "After test changes",
        "rendered from captured command output",
    ),
    (
        "slack-alert.png",
        "scripts/capture-all.ps1",
        "After an alert reaches the configured channel",
        "Slack firing alert",
    ),
    (
        "slack-resolved.png",
        "scripts/capture-all.ps1",
        "After the alert resolves",
        "Slack resolved alert",
    ),
    (
        "tempo-trace.png",
        "scripts/capture-all.ps1",
        "After trace data is available",
        "Grafana view of a trace found through the Tempo API",
    ),
]


def main() -> None:
    image_dir = ROOT / "docs" / "images"
    rows = [
        "# Screenshot file status",
        "",
        "See the [capture guide](../screenshots.md) for privacy requirements and setup.",
        (
            "Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "
            ".\\scripts\\capture-all.ps1` to refresh captures."
        ),
        (
            "Statuses reflect files present in this checkout. Terminal captures are rendered "
            "from captured command output."
        ),
        (
            "The original selected dashboard and deployment screenshots are preserved by "
            "the capture scripts when those files already exist."
        ),
        "",
        "| File | Status | Created by | Recapture when | Caption |",
        "|---|---|---|---|---|",
    ]
    for name, command, rerun, caption in IMAGES:
        status = "Present" if (image_dir / name).is_file() else "Missing"
        rows.append(f"| `{name}` | {status} | `{command}` | {rerun} | {caption} |")
    (image_dir / "README.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
