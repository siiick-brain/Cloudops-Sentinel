from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPECIFICATION = ROOT / "monitoring" / "prometheus" / "slo.yml"
OUTPUT = ROOT / "monitoring" / "prometheus" / "rules" / "slo.yml"


def build_rules() -> dict[str, object]:
    specification = yaml.safe_load(SPECIFICATION.read_text(encoding="utf-8"))
    availability = next(
        item for item in specification["objectives"] if item["name"] == "availability"
    )
    latency = next(item for item in specification["objectives"] if item["name"] == "latency")
    availability_budget = 1 - float(availability["target"]) / 100
    latency_budget = 1 - float(latency["target"]) / 100
    latency_limit = float(latency["threshold_ms"]) / 1000
    limit_text = f"{latency_limit:g}"
    groups = [
        {
            "name": "api-slo",
            "interval": "30s",
            "rules": [
                {
                    "record": "api:slo_requests:rate5m",
                    "expr": 'sum(rate(http_requests_total{service="api"}[5m]))',
                },
                {
                    "record": "api:slo_errors:rate5m",
                    "expr": 'sum(rate(http_requests_total{service="api",status=~"5.."}[5m]))',
                },
                {
                    "record": "api:slo_availability:ratio_rate5m",
                    "expr": (
                        "1 - (api:slo_errors:rate5m / clamp_min(api:slo_requests:rate5m, 1e-9))"
                    ),
                },
                {
                    "record": "api:slo_latency:ratio_rate5m",
                    "expr": (
                        "sum(rate(http_request_duration_seconds_bucket{"
                        f'service="api",le="{limit_text}"}}[5m])) '
                        "/ clamp_min(api:slo_requests:rate5m, 1e-9)"
                    ),
                },
                {
                    "record": "api:slo_requests:increase30d",
                    "expr": 'sum(increase(http_requests_total{service="api"}[30d]))',
                },
                {
                    "record": "api:slo_errors:increase30d",
                    "expr": (
                        'sum(increase(http_requests_total{service="api",status=~"5.."}[30d]))'
                    ),
                },
                {
                    "record": "api:slo_availability:ratio30d",
                    "expr": (
                        "1 - (api:slo_errors:increase30d / "
                        "clamp_min(api:slo_requests:increase30d, 1))"
                    ),
                },
                {
                    "record": "api:slo_latency:ratio30d",
                    "expr": (
                        "sum(increase(http_request_duration_seconds_bucket{"
                        f'service="api",le="{limit_text}"}}[30d])) '
                        "/ clamp_min(api:slo_requests:increase30d, 1)"
                    ),
                },
                {
                    "record": "api:slo_error_budget:remaining_ratio",
                    "expr": (
                        "1 - ((1 - api:slo_availability:ratio30d) "
                        f"/ {availability_budget:g})"
                    ),
                },
                {
                    "record": "api:slo_latency_error_budget:remaining_ratio",
                    "expr": (
                        "1 - ((1 - api:slo_latency:ratio30d) "
                        f"/ {latency_budget:g})"
                    ),
                },
            ],
        },
        {
            "name": "api-slo-burn",
            "interval": "30s",
            "rules": [
                _burn_alert(
                    "ApiAvailabilityBurnCritical",
                    "critical",
                    "availability",
                    availability_budget,
                    "14.4",
                    "5m",
                    "1h",
                    "2m",
                    "API availability is burning the error budget quickly",
                    "The multi-window burn rate exceeds 14.4 times the 30-day budget.",
                    "sentinel-golden-signals",
                ),
                _burn_alert(
                    "ApiAvailabilityBurnWarning",
                    "warning",
                    "availability",
                    availability_budget,
                    "6",
                    "30m",
                    "6h",
                    "5m",
                    "API availability is consuming the error budget",
                    "The multi-window burn rate exceeds 6 times the 30-day budget.",
                    "sentinel-slo",
                ),
                _burn_alert(
                    "ApiLatencyBurnWarning",
                    "warning",
                    "latency",
                    latency_budget,
                    "6",
                    "30m",
                    "6h",
                    "5m",
                    "API latency is consuming the latency objective budget",
                    (
                        f"Fewer than {latency['target']} percent of API requests are under "
                        f"{latency['threshold_ms']} ms."
                    ),
                    "sentinel-slo",
                    limit_text,
                ),
            ],
        },
    ]
    return {"groups": groups}


def _burn_alert(
    name: str,
    severity: str,
    objective: str,
    budget: float,
    multiplier: str,
    short_window: str,
    long_window: str,
    pending: str,
    summary: str,
    description: str,
    dashboard: str,
    latency_limit: str | None = None,
) -> dict[str, object]:
    if objective == "availability":
        short_rate = (
            'sum(rate(http_requests_total{service="api",status=~"5.."}['
            f"{short_window}])) / "
            'clamp_min(sum(rate(http_requests_total{service="api"}['
            f"{short_window}])), 1e-9)"
        )
        long_rate = (
            'sum(rate(http_requests_total{service="api",status=~"5.."}['
            f"{long_window}])) / "
            'clamp_min(sum(rate(http_requests_total{service="api"}['
            f"{long_window}])), 1e-9)"
        )
    else:
        assert latency_limit is not None
        short_rate = (
            '1 - (sum(rate(http_request_duration_seconds_bucket{service="api",le="'
            f'{latency_limit}"}}[{short_window}])) / '
            'clamp_min(sum(rate(http_requests_total{service="api"}['
            f"{short_window}])), 1e-9))"
        )
        long_rate = (
            '1 - (sum(rate(http_request_duration_seconds_bucket{service="api",le="'
            f'{latency_limit}"}}[{long_window}])) / '
            'clamp_min(sum(rate(http_requests_total{service="api"}['
            f"{long_window}])), 1e-9))"
        )
    threshold = f"{multiplier} * {budget:g}"
    return {
        "alert": name,
        "expr": f"({short_rate} > {threshold}) and ({long_rate} > {threshold})",
        "for": pending,
        "labels": {"severity": severity, "service": "api"},
        "annotations": {
            "summary": summary,
            "description": description,
            "value": '{{ printf "%.2f" $value }}',
            "runbook_url": (
                "https://github.com/siiick-brain/cloudops-sentinel/blob/main/docs/runbooks/"
                f"{name}.md"
            ),
            "dashboard_url": f"http://localhost:3000/d/{dashboard}",
        },
    }


def main() -> None:
    OUTPUT.write_text(
        yaml.safe_dump(build_rules(), sort_keys=False, allow_unicode=False),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
