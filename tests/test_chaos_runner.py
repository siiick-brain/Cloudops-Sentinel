import os

from chaos import run as chaos_runner
from chaos.run import find_firing_result


def test_firing_result_ignores_resolved_alerts_with_same_name():
    firing = {
        "alertname": "TargetDown",
        "status": "firing",
        "ticket_url": "http://localhost:8092/browse/MOCK-1",
    }
    results = [
        firing,
        {"alertname": "TargetDown", "status": "resolved", "ticket_url": ""},
    ]

    assert find_firing_result(results, "TargetDown") == firing


def test_firing_result_requires_expected_alert():
    results = [
        {
            "alertname": "ApiHighLatency",
            "status": "firing",
            "ticket_url": "http://localhost:8092/browse/MOCK-1",
        }
    ]

    assert find_firing_result(results, "TargetDown") == {}


def test_load_local_env_ignores_blank_values_for_token_defaults(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("CHAOS_TOKEN=\nROUTER_SHARED_TOKEN=\n", encoding="utf-8")
    monkeypatch.setattr(chaos_runner, "ROOT", tmp_path)
    monkeypatch.delenv("CHAOS_TOKEN", raising=False)
    monkeypatch.delenv("ROUTER_SHARED_TOKEN", raising=False)

    chaos_runner.load_local_env()

    assert os.getenv("CHAOS_TOKEN", "local-demo-token") == "local-demo-token"
    assert os.getenv("ROUTER_SHARED_TOKEN", "local-demo-token") == "local-demo-token"
