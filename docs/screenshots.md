# Screenshot guide

The expected image files are listed in [docs/images/README.md](images/README.md). None are currently present. Run `.\scripts\screenshot-prep.ps1` to print the capture cues and prepare the local mock stack. Save screenshots in `docs/images/`.

| Cue | File | What it shows and how to retake it | Redact |
|---|---|---|---|
| P2-01 | `P2-01-golden-signals.png` | In Grafana, open the golden-signals dashboard and capture request rate, error rate and latency panels. | Account labels and private host names. |
| P2-02 | `P2-02-slo-error-budget.png` | Open the SLO dashboard during a measured alert exercise and capture the objective and remaining budget. | Workspace URL and account labels. |
| P2-03 | `P2-03-node-container-health.png` | Open the node and container dashboard and capture CPU and memory panels. | Host names identifying a private system. |
| P2-04 | `P2-04-tempo-trace.png` | Open Tempo and capture a trace containing API and inventory spans. | Trace attributes with private data. |
| P2-05 | `P2-05-exemplar.png` | Open the API latency panel, select an exemplar and capture its trace link. | Trace attributes with private data. |
| P2-06 | `P2-06-prometheus-alert.png` | Open Prometheus alerts while a measured scenario alert is firing. | Workspace URL and private host names. |
| P2-07 | `P2-07-alertmanager-group.png` | Open Alertmanager and capture the grouped firing alert. | Workspace URL and private host names. |
| P2-08 | `P2-08-slack-alert.png` | Open the local Slack mock and capture a firing message with action buttons. | Tokens and private account information. |
| P2-09 | `P2-09-slack-resolved.png` | Recover the scenario, wait for the resolved mock message and capture it. | Tokens and private account information. |
| P2-10 | `P2-10-jira-ticket.png` | Open a Jira mock issue created by an alert and capture its summary, labels and links. | Tokens and account information. |
| P2-11 | `P2-11-jira-done.png` | Open the resolved mock issue and capture its Done state and resolution comment. | Tokens and account information. |
| P2-12 | `P2-12-chaos-output.png` | Run `python chaos/run.py latency` and capture the successful output. | Local account path and environment values. |
| P2-13 | `P2-13-ci-green.png` | After a workflow has run successfully, capture the completed workflow checks. | Private repository details. |
| P2-14 | `P2-14-runbook.png` | Open a runbook and capture the rendered symptoms, queries and mitigation sections. | Private repository details. |
| P2-15 | `P2-15-compose-healthy.png` | Run `docker compose ps` and capture the service status. | Local account path and private host names. |
| P2-16 | `P2-16-deployment-verification.png` | Run `.\scripts\verify-deployment.ps1` and capture the output and generated verification document. | Local account path. |
| P2-17 | `P2-17-grafana-login.png` | Open `https://localhost` and capture the Grafana login page with the address visible. | Hide any password entry. The localhost address needs no redaction. |

For alternate integration filenames, save P2-08 as `slack-alert.png`, P2-09 as `slack-resolved.png`, P2-10 as `jira-ticket.png` and P2-11 as `jira-resolved.png`.

Do not capture live integration data unless the owner has approved the display and all credentials and account details are redacted.
