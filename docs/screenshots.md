# Screenshot guide

Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\capture-all.ps1` from the repository root. Start the development stack with `docker compose up -d` first. The production-style stack intentionally does not publish Prometheus, Alertmanager or Tempo, so their page captures are skipped when only that stack is running. The script uses a fixed 1440 by 900 viewport and dark theme for browser captures.

The command captures Grafana dashboards returned by its API, Prometheus pages, Alertmanager, a trace found through Tempo and a Grafana exemplar view when available. It also renders real command output for Compose status, the chaos runner, pytest, the demo, deployment verification and the redacted Gitleaks history scan. Each result is reported as Captured, Skipped or Failed.

Captures are written to `docs/images/`. Existing filenames are retained. The [image status list](images/README.md) shows the required evidence and when to recapture it. Terminal images are rendered from captured command output. Text in those images is not redacted or summarized.

## Private integrations

Set `SLACK_CHANNEL_URL` and `JIRA_SITE_URL` in the ignored `.env` file. Run `.\.venv\Scripts\python.exe scripts\save_login.py` to open visible Slack and Jira browser pages and save session state under ignored `private/auth/`. That session state is a credential. Delete it after capture.

Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\capture-all.ps1` again to capture Slack firing and resolved messages and the Jira ticket and Done view. The Jira ticket URL must be recorded in `docs/live-verification.md`. If a session is missing or expired or a ticket URL is not recorded, the corresponding image is skipped with a reason.

Before each integration capture, the script blurs the user email, avatar, workspace and site identity and token-like text. The browser chrome is not included in page screenshots. After capture, OCR checks configured emails and service hosts and common token patterns. If OCR detects a match, the image is deleted and reported as Failed. If pytesseract or the Tesseract executable is missing, the result reports that the OCR check was skipped.

## GitHub pages and GIF

GitHub pages are captured without login only when `gh repo view` confirms that the repository is public. Private or unconfigured repositories are skipped.

The demo GIF records the SLO dashboard during a short latency scenario. It is rendered at 12 fps and must remain at most 5 MB. If ffmpeg is unavailable, install it with `winget install Gyan.FFmpeg`, then rerun the capture command.
