# Screenshot guide

The README gallery uses the selected original screenshots in `docs/images/`. The capture command preserves those files when they already exist, so a rerun cannot replace the gallery with an empty dashboard.

Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\capture-all.ps1` from the repository root while the development Compose stack is running. The browser viewport is 1440 by 900, the browser theme is dark and dashboard time ranges use the preceding hour. The script starts a short latency scenario while it captures the monitoring pages. Each image is reported as Captured, Skipped or Failed with a reason.

## Capture scripts

Use `scripts/capture-all.ps1` as the single automated capture command. It runs these capture modules in order:

| Script | Captures |
|---|---|
| `scripts/capture_pages.py` | Grafana dashboards and login, Prometheus alerts and targets, Alertmanager, a Tempo trace and an exemplar view |
| `scripts/capture_integrations.py` | Slack firing and resolved messages and Jira ticket and Done views |
| `scripts/capture_github.py` | Public repository, Actions, runbook and contributors pages |
| `scripts/record_demo.py` | SLO dashboard video converted to `demo.gif` |
| `scripts/terminal_shot.py` | PNGs rendered from real command output |

`scripts/capture_support.py` shares image validation and saving between the modules. It preserves the nine selected README screenshots when those files already exist. Run `scripts/save_login.py` separately when the Slack or Jira browser session needs to be created or renewed.

`scripts/screenshot-prep.ps1` is a separate manual preparation flow and is not called by `capture-all.ps1`. It takes the development Compose stack down before starting the production-style stack.

## Selected screenshots

| File | What it shows | Retake |
|---|---|---|
| `grafana-golden-signals.png` | API request rate and p95 latency. The selected capture has no error-rate data. | Confirm the dashboard panels have data before capturing. Move the existing file into ignored `private/` storage before running the capture command. |
| `grafana-distributed-traces.png` | API and inventory trace rates over time. | Confirm both services are sending spans before capturing. |
| `grafana-node-container-health.png` | Node CPU and container memory metrics. | Confirm cAdvisor returns named container metrics before capturing. |
| `grafana-slo-error-budget.png` | Latency objective and remaining budget. The availability panel has no data in the selected capture. | Confirm the desired SLO panels have data before capturing. |
| `prometheus-targets-up.png` | Prometheus target health. | Confirm targets are in the intended state before capturing. |
| `prometheus-container-cpu-metrics.png` | Container CPU usage over time. | Confirm cAdvisor samples have a container name before capturing. |
| `prometheus-alert-rules.png` | Platform alert rules and states. | Run a scenario only when a firing alert is needed. |
| `prometheus-cpu-alert-firing.png` | Prometheus alert details. The selected capture shows NodeDiskHigh, not a CPU alert. | Capture only after confirming the alert name and details in the page. |
| `P2-16-deployment-verification.png` | Original Compose startup output. | Run deployment verification and inspect the output before replacing the selected image. |

Move an existing selected image to ignored `private/` storage before retaking it. The capture script writes to the original filename only when that file is absent. Review the new image before moving it into the README gallery.

The [image status list](images/README.md) lists each expected output as Present or Missing with its command and recapture guidance. Automated captures that are not in the selected gallery remain separate files and are not linked from the README.

## Terminal images

`scripts/terminal_shot.py` runs the displayed command and renders its captured stdout, stderr and exit code to a PNG. It preserves output text, wraps lines without changing their characters and prints a UTC timestamp on the last line. Terminal images use a monospace font and a dark background. Their README caption is `rendered from captured command output`.

## Private Slack and Jira captures

Set `SLACK_CHANNEL_URL` and `JIRA_SITE_URL` in the ignored `.env` file. Run `.\.venv\Scripts\python.exe scripts\save_login.py` to open visible Slack and Jira pages and save session state under ignored `private/auth/`. The state is a credential. Delete it after capture.

The capture script reuses those sessions to capture firing and resolved Slack messages and the Jira ticket and Done view. The ticket URL must be recorded in `docs/live-verification.md`. If a session is missing or expired or a ticket URL is not recorded, the corresponding image is skipped with instructions to run `save_login.py`.

Before each integration capture, the script blurs matching email addresses, workspace names, service hosts, avatars and token-like text. The screenshot contains the browser viewport, not browser chrome. After capture, OCR checks configured emails and service hosts and common token patterns. A detected match deletes the image and reports Failed. If pytesseract or the Tesseract executable is missing, the result reports that the OCR check was skipped.

## GitHub pages and GIF

GitHub pages are captured without login only when `gh repo view` reports that the repository is public. Otherwise each page is skipped with a reason.

The demo GIF records the SLO dashboard during a short latency scenario. It is rendered at 12 fps and must remain at most 5 MB. If ffmpeg is unavailable, install it with `winget install Gyan.FFmpeg`, then rerun the capture command.
