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
        lambda alert_name, timeout, since: (
            {"prometheus": True, "alertmanager": True, "jira": True, "slack": True},
            {"ticket_url": "http://localhost:8092/browse/MOCK-1", "slack_timestamp": "1"},
        ),
    )
    monkeypatch.setattr(chaos_runner, "check_router_mode", lambda: None)
    monkeypatch.setattr(chaos_runner, "wait_for_steady_state", lambda alert_name, timeout: None)
    monkeypatch.setattr(chaos_runner, "recover", lambda scenario: None)
    monkeypatch.setattr(chaos_runner, "RESULTS", tmp_path)

    result = chaos_runner.run("latency", duration_override=90)

    assert injected_durations == [90]
    assert alert_timeouts == [90]
    assert result["status"] == "passed"


class _Health:
    def __init__(self, mode):
        self.mode = mode

    def json(self):
        return {"status": "ok", "mode": self.mode}


def test_runner_refuses_mode_mismatch(monkeypatch):
    import pytest

    monkeypatch.setattr(chaos_runner, "INTEGRATION_MODE", "mock")
    monkeypatch.setattr(chaos_runner.requests, "get", lambda *a, **k: _Health("real"))
    with pytest.raises(RuntimeError, match="pass --live"):
        chaos_runner.check_router_mode()

    monkeypatch.setattr(chaos_runner.requests, "get", lambda *a, **k: _Health("mock"))
    chaos_runner.check_router_mode()


def test_runner_defaults_to_mock_even_when_env_says_real(monkeypatch):
    import importlib

    monkeypatch.setenv("INTEGRATION_MODE", "real")
    assert importlib.reload(chaos_runner).INTEGRATION_MODE == "mock"


def test_alert_wait_survives_transient_errors(monkeypatch):
    calls = []

    def flaky(name):
        calls.append(1)
        if len(calls) == 1:
            raise chaos_runner.requests.ConnectionError("restarting")
        return True

    monkeypatch.setattr(chaos_runner, "alert_is_active", flaky)
    monkeypatch.setattr(chaos_runner.time, "sleep", lambda s: None)
    assert chaos_runner.wait_for_alert("X", 30)
    assert len(calls) == 2


def test_stale_results_from_earlier_runs_are_ignored():
    old = {"alertname": "X", "status": "firing", "ticket_url": "u", "routed_at": "100"}
    new = {**old, "routed_at": "200"}
    assert find_firing_result([old], "X", since=150) == {}
    assert find_firing_result([old, new], "X", since=150) == new


def test_steady_state_requires_quiet_alert(monkeypatch):
    import pytest

    monkeypatch.setattr(chaos_runner, "alert_is_active", lambda name: True)
    monkeypatch.setattr(chaos_runner.time, "sleep", lambda s: None)
    times = iter([0, 0, 1000])
    monkeypatch.setattr(chaos_runner.time, "monotonic", lambda: next(times))
    with pytest.raises(RuntimeError, match="Steady state not reached"):
        chaos_runner.wait_for_steady_state("X", 600)


def test_steady_state_waits_for_resolved_notification(monkeypatch):
    class Latest:
        def __init__(self, statuses):
            self.statuses = statuses

        def raise_for_status(self):
            pass

        def json(self):
            return {"results": [{"alertname": "X", "status": s} for s in self.statuses]}

    monkeypatch.setattr(chaos_runner.requests, "get", lambda *a, **k: Latest(["firing"]))
    assert chaos_runner.routed_as_firing("X")
    monkeypatch.setattr(
        chaos_runner.requests, "get", lambda *a, **k: Latest(["firing", "resolved"])
    )
    assert not chaos_runner.routed_as_firing("X")
    monkeypatch.setattr(chaos_runner.requests, "get", lambda *a, **k: Latest([]))
    assert not chaos_runner.routed_as_firing("X")


def test_committed_chaos_results_hold_only_local_urls():
    import json
    import re

    for path in (chaos_runner.RESULTS).glob("*.json"):
        text = path.read_text(encoding="utf-8")
        json.loads(text)
        for url in re.findall(r"https?://[^\s\"]+", text):
            assert url.startswith(("http://localhost", "http://127.0.0.1")), (path.name, url)


def test_integration_wait_covers_alertmanager_group_interval():
    import re

    import yaml

    config = yaml.safe_load((chaos_runner.ROOT / "monitoring" / "alertmanager.yml").read_text())
    route = config["route"]

    def seconds(value):
        number, unit = re.fullmatch(r"(\d+)([smh])", value).groups()
        return int(number) * {"s": 1, "m": 60, "h": 3600}[unit]

    assert chaos_runner.INTEGRATION_TIMEOUT > seconds(route["group_interval"]) + seconds(
        route["group_wait"]
    )
