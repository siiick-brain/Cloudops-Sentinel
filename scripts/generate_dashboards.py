import json
from pathlib import Path

from grafana_foundation_sdk.builders.dashboard import Dashboard
from grafana_foundation_sdk.builders.prometheus import Dataquery as PrometheusQuery
from grafana_foundation_sdk.builders.timeseries import Panel as Timeseries
from grafana_foundation_sdk.cog.encoder import JSONEncoder
from grafana_foundation_sdk.models.common import TimeZoneBrowser

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "monitoring" / "grafana" / "dashboards"

PANELS = {
    "golden-signals": [
        ("Request rate", 'sum(rate(http_requests_total{service=~"api|inventory"}[5m]))', "req/s"),
        (
            "Error rate",
            'sum(rate(http_requests_total{service=~"api|inventory",status=~"5.."}[5m]))',
            "req/s",
        ),
        (
            "API p95 latency",
            "histogram_quantile(0.95, sum by (le) "
            '(rate(http_request_duration_seconds_bucket{service="api"}[5m])))',
            "s",
        ),
    ],
    "slo": [
        ("Availability SLO, 30 days", "api:slo_availability:ratio30d", "ratio"),
        ("Latency SLO, 30 days", "api:slo_latency:ratio30d", "ratio"),
        ("Availability budget remaining", "api:slo_error_budget:remaining_ratio", "ratio"),
        ("Latency budget remaining", "api:slo_latency_error_budget:remaining_ratio", "ratio"),
        ("Availability short-window trend", "api:slo_availability:ratio_rate5m", "ratio"),
        ("Latency short-window trend", "api:slo_latency:ratio_rate5m", "ratio"),
    ],
    "node-container": [
        ("Node CPU", '1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))', "ratio"),
        ("Container memory", "sum(container_memory_working_set_bytes) by (name)", "bytes"),
    ],
    "traces": [
        (
            "Trace rate by service",
            "sum by (service_name) (rate(traces_span_metrics_calls_total[5m]))",
            "spans/s",
        ),
    ],
}

DASHBOARDS = {
    "sentinel-golden-signals": ("Service golden signals", "golden-signals"),
    "sentinel-slo": ("SLO and error budget", "slo"),
    "sentinel-node-container": ("Node and container health", "node-container"),
    "sentinel-traces": ("Distributed traces", "traces"),
}


def build_dashboard(uid: str, title: str, panel_group: str) -> dict[str, object]:
    dashboard = (
        Dashboard(title)
        .uid(uid)
        .tags(["operations", "slo", "traces"])
        .refresh("10s")
        .time("now-1h", "now")
        .timezone(TimeZoneBrowser)
    )
    for panel_title, expression, unit in PANELS[panel_group]:
        legend = "{{service_name}}" if "service_name" in expression else "{{service}}"
        dashboard.with_panel(
            Timeseries()
            .title(panel_title)
            .unit(unit)
            .with_target(PrometheusQuery().expr(expression).legend_format(legend))
        )
    payload = json.loads(JSONEncoder(sort_keys=True, indent=2).encode(dashboard.build()))
    payload["id"] = None
    payload["version"] = 1
    for index, panel in enumerate(payload["panels"]):
        panel["id"] = index + 1
        panel["datasource"] = {"type": "prometheus", "uid": "prometheus"}
        panel["gridPos"] = {"h": 8, "w": 12, "x": index % 2 * 12, "y": index // 2 * 8}
        panel["targets"][0]["refId"] = "A"
        panel["targets"][0]["exemplar"] = panel["title"] == "API p95 latency"
    payload["schemaVersion"] = 39
    payload["links"] = [
        {
            "title": "Tempo traces",
            "url": "http://localhost:3000/explore?left=%7B%22datasource%22:%22tempo%22%7D",
        }
    ]
    return payload


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for uid, (title, panel_group) in DASHBOARDS.items():
        target = OUTPUT / f"{uid}.json"
        target.write_text(
            json.dumps(build_dashboard(uid, title, panel_group), indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )


if __name__ == "__main__":
    main()
