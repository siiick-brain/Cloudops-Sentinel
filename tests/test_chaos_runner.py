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


def test_duration_override_caps_chaos_scenario_without_changing_configuration(
    tmp_path, monkeypatch
):
    injected_durations = []
    alert_timeouts = []
    monkeypatch.setattr(
        chaos_runner,
        "inject",
        lambda scenario, duration: injected_durations.append(duration),
    )
    monkeypatch.setattr(
        chaos_runner,
        "wait_for_alert",
        lambda alert_name, timeout: alert_timeouts.append(timeout) or 1,
    )
    monkeypatch.setattr(
        chaos_runner,
        "wait_for_integrations",
        lambda alert_name, timeout: (
            {"prometheus": True, "alertmanager": True, "jira": True, "slack": True},
            {"ticket_url": "http://localhost:8092/browse/MOCK-1", "slack_timestamp": "1"},
        ),
    )
    monkeypatch.setattr(chaos_runner, "recover", lambda scenario: None)
    monkeypatch.setattr(chaos_runner, "RESULTS", tmp_path)

    result = chaos_runner.run("latency", duration_override=90)

    assert injected_durations == [90]
    assert alert_timeouts == [90]
    assert result["status"] == "passed"
