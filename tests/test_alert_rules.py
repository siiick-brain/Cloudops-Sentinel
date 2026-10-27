import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_every_alert_has_runbook():
    alert_names = []
    for rule_file in (ROOT / "monitoring" / "prometheus" / "rules").glob("*.yml"):
        if rule_file.name.endswith(".test.yml"):
            continue
        document = yaml.safe_load(rule_file.read_text(encoding="utf-8"))
        for group in document["groups"]:
            for rule in group["rules"]:
                if "alert" in rule:
                    alert_names.append(rule["alert"])
                    assert rule["annotations"].get("runbook_url")
    runbooks = {path.stem for path in (ROOT / "docs" / "runbooks").glob("*.md")}
    assert set(alert_names) <= runbooks


def test_chaos_scenarios_reference_defined_alerts():
    alert_names = set()
    for rule_file in (ROOT / "monitoring" / "prometheus" / "rules").glob("*.yml"):
        if rule_file.name.endswith(".test.yml"):
            continue
        document = yaml.safe_load(rule_file.read_text(encoding="utf-8"))
        for group in document["groups"]:
            alert_names.update(
                rule["alert"] for rule in group["rules"] if "alert" in rule
            )

    for scenario_file in (ROOT / "chaos").glob("*.yml"):
        scenario = yaml.safe_load(scenario_file.read_text(encoding="utf-8"))
        assert scenario["expected_alert"] in alert_names


def test_dashboard_output_matches_generator():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/generate_dashboards.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    dashboards = {
        json.loads(path.read_text(encoding="utf-8"))["uid"]: json.loads(
            path.read_text(encoding="utf-8")
        )
        for path in (ROOT / "monitoring" / "grafana" / "dashboards").glob("*.json")
    }
    assert set(dashboards) == {
        "sentinel-golden-signals",
        "sentinel-slo",
        "sentinel-node-container",
        "sentinel-traces",
    }
    assert len(dashboards["sentinel-golden-signals"]["panels"]) == 3
    assert len(dashboards["sentinel-slo"]["panels"]) == 6
    trace_query = dashboards["sentinel-traces"]["panels"][0]["targets"][0]["expr"]
    assert "traces_span_metrics_calls_total" in trace_query


def test_slo_rules_match_spec_generator():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/generate_slo_rules.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
