import json
import os
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    source = ROOT / ".env"
    if not source.is_file():
        raise RuntimeError(".env is required")
    for line in source.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#") or "=" not in value:
            continue
        key, content = value.split("=", 1)
        os.environ.setdefault(key.strip(), content.strip().strip("\"'"))


def main() -> None:
    load_env()
    if os.getenv("INTEGRATION_MODE") != "real":
        raise RuntimeError("Set INTEGRATION_MODE=real in .env")
    token = os.environ.get("ROUTER_SHARED_TOKEN", "local-demo-token")
    response = requests.get(
        "http://localhost:8090/latest",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    result = next(
        (item for item in reversed(results) if item.get("alertname") == "ApiHighLatency"),
        None,
    )
    if not result or not result.get("ticket_url"):
        raise RuntimeError("No Jira ticket result was returned by alert-router")
    chaos_result = ROOT / "artifacts" / "chaos-results" / "latency.json"
    measurements = json.loads(chaos_result.read_text(encoding="utf-8"))
    timestamp = result.get("slack_timestamp")
    now = datetime.now(UTC).date().isoformat()
    issue_key = result.get("issue_key", "Not returned")
    state = "Verified" if timestamp else "Not verified, Slack webhook returned no message timestamp"
    content = (
        "# Live integration verification\n\n"
        f"Status: {state}.\n\n"
        f"Date: {now}.\n\n"
        f"Jira issue key: {issue_key}. The workspace URL is not stored here.\n\n"
        f"Slack message timestamp: {timestamp or 'Not returned by incoming webhook'}.\n\n"
        "Fault injection to ticket: "
        f"{measurements.get('ticket_seconds', 'Not measured')} seconds.\n"
    )
    (ROOT / "docs" / "live-verification.md").write_text(content, encoding="utf-8")
    print(f"Jira issue URL: {result['ticket_url']}")
    print(
        "Slack message timestamp: "
        f"{timestamp or 'Not available from the incoming webhook response'}"
    )
    print(
        f"Fault injection to ticket: {measurements.get('ticket_seconds', 'Not measured')} seconds"
    )
    if not timestamp:
        raise RuntimeError("Slack incoming webhooks do not return a message timestamp")


if __name__ == "__main__":
    main()
