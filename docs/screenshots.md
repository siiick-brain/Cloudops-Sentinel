# Screenshot capture steps

Run `.\scripts\screenshot-prep.ps1` to start the local demo stack, send traffic and trigger a latency scenario. The script then starts the local production-style deployment and verifies its network controls. It prints cues for all captures. Save each image under `docs/images/` using the listed filename. Hide access tokens, email addresses, workspace URLs and site URLs in every capture. Do not expose webhook URLs, Jira API tokens, customer data or browser profile details.

| Cue | File | Capture steps | Redact |
|---|---|---|---|
| P2-01 | `P2-01-golden-signals.png` | Open Grafana, select Operations and capture the request rate, error rate and latency panels. | Any account or workspace label. |
| P2-02 | `P2-02-slo-error-budget.png` | Open the SLO panels during an active latency or error burn and capture the objective and remaining budget. | Workspace URL and account labels. |
| P2-03 | `P2-03-node-container-health.png` | Open the node and container panels and capture CPU, memory and container use. | Host names that identify a private system. |
| P2-04 | `P2-04-tempo-trace.png` | Open Tempo, locate a recent API trace and capture its API and inventory spans. | Trace attributes with private data. |
| P2-05 | `P2-05-exemplar.png` | Open the latency panel, select an exemplar and capture the trace link. | Trace attributes with private data. |
| P2-06 | `P2-06-prometheus-alert.png` | Open Prometheus Alerts while a chaos alert is firing. | Workspace URL and private host names. |
| P2-07 | `P2-07-alertmanager-group.png` | Open Alertmanager and capture the grouped firing alert. | Workspace URL and private host names. |
| P2-08 | `P2-08-slack-alert.png` | Open the Slack alert channel and capture the firing message and action buttons. | Tokens, email and workspace URL. |
| P2-09 | `P2-09-slack-resolved.png` | Recover the scenario, wait for the resolved message and capture it. | Tokens, email and workspace URL. |
| P2-10 | `P2-10-jira-ticket.png` | Open the Jira issue created by the alert and capture summary, labels and links. | Tokens, email and site URL. |
| P2-11 | `P2-11-jira-done.png` | Open the resolved Jira issue and capture its Done status and resolution comment. | Tokens, email and site URL. |
| P2-12 | `P2-12-chaos-output.png` | Capture the terminal output from a successful `python chaos/run.py latency` run. | Local account path and environment values. |
| P2-13 | `P2-13-ci-green.png` | Open the successful workflow run and capture completed checks. | Repository or organization details if private. |
| P2-14 | `P2-14-runbook.png` | Open a runbook in the GitHub file view and capture the rendered sections. | Repository or organization details if private. |
| P2-15 | `P2-15-compose-healthy.png` | Run `docker compose ps` and capture the healthy service status. | Local account path and private host names. |
| P2-16 | `P2-16-deployment-verification.png` | Capture the output from `.\scripts\verify-deployment.ps1` and `docs/deployment-verification.md`. | Local account path. |
| P2-17 | `P2-17-grafana-login.png` | Open the Grafana login page at `https://localhost` and capture it with the address visible. | Nothing in the localhost address needs blurring. Hide any password entry. |

For the integration captures, also save P2-08 as `slack-alert.png`, P2-09 as `slack-resolved.png`, P2-10 as `jira-ticket.png` and P2-11 as `jira-resolved.png` in this directory.

Screenshot status: Not captured.
