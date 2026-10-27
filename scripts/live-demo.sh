#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
    printf '%s\n' "Not verified: create .env with Jira Cloud and Slack credentials, set INTEGRATION_MODE=real, then rerun."
    exit 2
fi
env_config=$(sed 's/\r$//' .env)
if ! printf '%s\n' "$env_config" | grep -Eq '^INTEGRATION_MODE=real$'; then
    printf '%s\n' "Not verified: set INTEGRATION_MODE=real in .env before a live run."
    exit 2
fi
for key in JIRA_BASE_URL JIRA_EMAIL JIRA_API_TOKEN JIRA_PROJECT_KEY SLACK_WEBHOOK_URL; do
    if ! printf '%s\n' "$env_config" | grep -Eq "^${key}=.+"; then
        printf 'Not verified: .env must define %s before a live run.\n' "$key"
        exit 2
    fi
done
docker compose up -d --build
python chaos/run.py latency
python scripts/live_result.py
