import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts" / "chaos-results"


def load_local_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_local_env()
API = os.getenv("API_URL", "http://localhost:8000")
PROMETHEUS = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
ALERTMANAGER = os.getenv("ALERTMANAGER_URL", "http://localhost:9093")
ROUTER_TOKEN = os.getenv("ROUTER_SHARED_TOKEN", "local-demo-token")
CHAOS_TOKEN = os.getenv("CHAOS_TOKEN", "local-demo-token")
INTEGRATION_MODE = os.getenv("INTEGRATION_MODE", "mock")


def docker(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def inject(scenario: str, duration: int) -> None:
    if scenario == "latency":
        requests.post(
            f"{API}/chaos",
            headers={"X-Chaos-Token": CHAOS_TOKEN},
            json={"latency_seconds": 0.6, "error_rate": 0},
            timeout=10,
        ).raise_for_status()
    elif scenario == "errors":
        requests.post(
            f"{API}/chaos",
            headers={"X-Chaos-Token": CHAOS_TOKEN},
            json={"latency_seconds": 0, "error_rate": 1},
            timeout=10,
        ).raise_for_status()
    elif scenario == "backend-killed":
        docker("stop", "backend")
    elif scenario in {"cpu-stress", "memory-pressure", "disk-fill"}:
        docker("--profile", "chaos", "up", "-d", "chaos-tools")
        command = {
            "cpu-stress": ["stress-ng", "--cpu", "2", "--timeout", f"{duration}s"],
            "memory-pressure": [
                "stress-ng",
                "--vm",
                "1",
                "--vm-bytes",
                "128M",
                "--timeout",
                f"{duration}s",
            ],
            "disk-fill": [
                "sh",
                "-c",
                "dd if=/dev/zero of=/bounded-file bs=1M count=64 && sleep 180",
            ],
        }[scenario]
        docker("exec", "-d", "chaos-tools", *command)
    elif scenario == "network-delay":
        response = requests.post(
            "http://localhost:8474/proxies/inventory/toxics",
            json={
                "name": "latency",
                "type": "latency",
                "stream": "downstream",
                "attributes": {"latency": 700},
            },
            timeout=10,
        )
        response.raise_for_status()
    else:
        raise ValueError(f"Unknown scenario: {scenario}")


def recover(scenario: str) -> None:
    if scenario in {"latency", "errors"}:
        requests.delete(
            f"{API}/chaos",
            headers={"X-Chaos-Token": CHAOS_TOKEN},
            timeout=10,
        ).raise_for_status()
    elif scenario == "backend-killed":
        docker("start", "backend")
    elif scenario == "network-delay":
        requests.delete(
            "http://localhost:8474/proxies/inventory/toxics/latency", timeout=10
        ).raise_for_status()
    elif scenario == "disk-fill":
        docker("exec", "chaos-tools", "rm", "-f", "/bounded-file")
        docker("stop", "chaos-tools")
    elif scenario in {"cpu-stress", "memory-pressure"}:
        docker("stop", "chaos-tools")


def alert_is_active(alert_name: str) -> bool:
    response = requests.get(f"{ALERTMANAGER}/api/v2/alerts", timeout=5)
    response.raise_for_status()
    return any(alert.get("labels", {}).get("alertname") == alert_name for alert in response.json())


def wait_for_alert(alert_name: str, timeout: int) -> float:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if alert_is_active(alert_name):
            return time.monotonic()
        time.sleep(5)
    raise TimeoutError(f"Expected alert did not fire: {alert_name}")


def find_firing_result(
    results: list[dict[str, Any]], alert_name: str
) -> dict[str, Any]:
    return next(
        (
            item
            for item in reversed(results)
            if item.get("alertname") == alert_name
            and item.get("status") == "firing"
            and item.get("ticket_url")
        ),
        {},
    )


def check_integrations(alert_name: str) -> tuple[dict[str, bool], dict[str, str | None]]:
    prom = requests.get(
        f"{PROMETHEUS}/api/v1/alerts",
        timeout=5,
    )
    prom.raise_for_status()
    prometheus_active = any(
        item.get("labels", {}).get("alertname") == alert_name
        for item in prom.json().get("data", {}).get("alerts", [])
    )
    latest = requests.get(
        "http://localhost:8090/latest",
        headers={"Authorization": f"Bearer {ROUTER_TOKEN}"},
        timeout=5,
    )
    latest.raise_for_status()
    results = latest.json().get("results", [])
    routed = find_firing_result(results, alert_name)
    checks = {
        "prometheus": prometheus_active,
        "alertmanager": alert_is_active(alert_name),
        "jira": bool(routed.get("ticket_url")),
        "slack": bool(routed)
        and (INTEGRATION_MODE == "real" or bool(routed.get("slack_timestamp"))),
    }
    if INTEGRATION_MODE == "mock":
        jira = requests.get(
            "http://localhost:8092/rest/api/3/search",
            params={"jql": "project = MOCK"},
            timeout=5,
        )
        jira.raise_for_status()
        slack = requests.get("http://localhost:8091/messages", timeout=5)
        slack.raise_for_status()
        checks["jira"] = checks["jira"] and jira.json().get("total", 0) > 0
        checks["slack"] = checks["slack"] and bool(slack.json().get("messages"))
    return checks, routed


def wait_for_integrations(
    alert_name: str, timeout: int
) -> tuple[dict[str, bool], dict[str, str | None]]:
    deadline = time.monotonic() + timeout
    checks: dict[str, bool] = {}
    routed: dict[str, str | None] = {}
    while time.monotonic() < deadline:
        checks, routed = check_integrations(alert_name)
        if all(checks.values()):
            return checks, routed
        time.sleep(3)
    return checks, routed


def run(scenario: str) -> dict[str, Any]:
    source = ROOT / "chaos" / f"{scenario}.yml"
    specification = yaml.safe_load(source.read_text(encoding="utf-8"))
    started_at = datetime.now(UTC)
    start = time.monotonic()
    expected = specification["expected_alert"]
    result: dict[str, Any] = {
        "scenario": scenario,
        "started_at": started_at.isoformat(),
        "expected_alert": expected,
        "status": "failed",
    }
    try:
        inject(scenario, int(specification["duration_seconds"]))
        injection_time = time.monotonic()
        result["injection_seconds"] = injection_time - start
        fired_at = wait_for_alert(expected, int(specification["duration_seconds"]))
        result["alert_seconds"] = fired_at - injection_time
        checks, routed = wait_for_integrations(expected, 90)
        result["integration_checks"] = checks
        result["ticket_seconds"] = time.monotonic() - injection_time
        result["ticket_url"] = routed.get("ticket_url")
        result["slack_timestamp"] = routed.get("slack_timestamp")
        if not all(result["integration_checks"].values()):
            raise RuntimeError(f"An integration check did not pass: {result['integration_checks']}")
        result["status"] = "passed"
    finally:
        recover(scenario)
        result["completed_at"] = datetime.now(UTC).isoformat()
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / f"{scenario}.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scenario",
        choices=[
            "latency",
            "errors",
            "backend-killed",
            "cpu-stress",
            "memory-pressure",
            "disk-fill",
            "network-delay",
        ],
    )
    args = parser.parse_args()
    try:
        result = run(args.scenario)
    except Exception as exc:
        print(f"Chaos scenario {args.scenario} failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(result))


if __name__ == "__main__":
    main()
