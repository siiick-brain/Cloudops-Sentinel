from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_python_healthchecks_allow_slow_docker_hosts():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    python_services = {
        "api",
        "backend",
        "loadgen",
        "alert-router",
        "mock-slack",
        "mock-jira",
    }

    for service_name in python_services:
        healthcheck = compose["services"][service_name]["healthcheck"]
        assert healthcheck["timeout"] == "10s"
