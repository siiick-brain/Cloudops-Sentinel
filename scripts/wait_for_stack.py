import sys
import time

import requests

READY_ENDPOINTS = {
    "api": "http://localhost:8000/readyz",
    "backend": "http://localhost:8001/readyz",
    "prometheus": "http://localhost:9090/-/ready",
    "alertmanager": "http://localhost:9093/-/ready",
    "grafana": "http://localhost:3000/api/health",
    "tempo": "http://localhost:3200/ready",
}
EXPECTED_JOBS = {
    "prometheus",
    "alertmanager",
    "api",
    "backend",
    "alert-router",
    "mock-jira",
    "mock-slack",
    "grafana",
    "node-exporter",
    "cadvisor",
    "tempo",
    "otel-collector",
}


def endpoint_ready(url: str) -> bool:
    try:
        return requests.get(url, timeout=3).ok
    except requests.RequestException:
        return False


def targets_ready() -> bool:
    try:
        response = requests.get("http://localhost:9090/api/v1/targets", timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return False
    targets = response.json().get("data", {}).get("activeTargets", [])
    up_jobs = {
        target.get("labels", {}).get("job")
        for target in targets
        if target.get("health") == "up"
    }
    return EXPECTED_JOBS <= up_jobs


def main() -> None:
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        services_ready = all(endpoint_ready(url) for url in READY_ENDPOINTS.values())
        if services_ready and targets_ready():
            print("All expected service endpoints and Prometheus targets are healthy.")
            return
        time.sleep(3)
    print("The stack did not reach readiness before the four minute timeout.", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
