from __future__ import annotations

import json
import time
from io import BytesIO
from urllib.parse import quote, urlencode

import requests
import urllib3
from capture_support import CaptureResult, emit, read_env, save_png
from PIL import Image

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VIEWPORT = {"width": 1440, "height": 900}
DASHBOARD_FILES = {
    "golden": "grafana-golden-signals.png",
    "slo": "grafana-slo-error-budget.png",
    "node": "grafana-node-container-health.png",
    "trace": "grafana-distributed-traces.png",
}


def fetch_json(url: str, auth: tuple[str, str] | None = None) -> object:
    response = requests.get(url, auth=auth, timeout=5, verify=False)
    response.raise_for_status()
    return response.json()


def capture_image(page: object, url: str, name: str, env: dict[str, str]) -> CaptureResult:
    page.goto(url, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1200)
    image = Image.open(BytesIO(page.screenshot(full_page=False)))
    return save_png(image, name, env)


def skip(name: str, reason: str) -> CaptureResult:
    return CaptureResult(name, "Skipped", reason)


def dashboard_file(title: str) -> str | None:
    lower = title.casefold()
    for key, filename in DASHBOARD_FILES.items():
        if key == "golden" and "golden" in lower:
            return filename
        if key == "slo" and "slo" in lower:
            return filename
        if key == "node" and ("node" in lower or "container" in lower):
            return filename
        if key == "trace" and "trace" in lower:
            return filename
    return None


def capture_grafana(browser: object, env: dict[str, str]) -> list[CaptureResult]:
    expected = list(DASHBOARD_FILES.values()) + [
        "P2-17-grafana-login.png",
        "grafana-exemplar.png",
        "tempo-trace.png",
    ]
    password = env.get("GRAFANA_ADMIN_PASSWORD", "")
    if not password:
        return [skip(name, "GRAFANA_ADMIN_PASSWORD is not set in .env") for name in expected]

    username = env.get("GRAFANA_ADMIN_USER", "admin")
    candidates = []
    configured = env.get("GRAFANA_URL", "").rstrip("/")
    if configured:
        candidates.append(configured)
    candidates.extend(["https://localhost", "http://localhost:3000"])
    session = requests.Session()
    session.auth = (username, password)
    session.verify = False
    session.headers["Accept"] = "application/json"
    base = ""
    dashboards: list[dict[str, str]] = []
    for candidate in dict.fromkeys(candidates):
        try:
            response = session.get(f"{candidate}/api/search?type=dash-db", timeout=5)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, list):
                base = candidate
                dashboards = [
                    item
                    for item in payload
                    if isinstance(item, dict)
                    and isinstance(item.get("title"), str)
                    and isinstance(item.get("url"), str)
                ]
                break
        except (requests.RequestException, ValueError):
            continue
    if not base:
        reason = "Grafana API is unavailable at the configured or local URLs"
        return [skip(name, reason) for name in expected]

    results: list[CaptureResult] = []
    context = browser.new_context(
        ignore_https_errors=True,
        viewport=VIEWPORT,
        color_scheme="dark",
    )
    login_page = context.new_page()
    try:
        login_page.goto(f"{base}/login", wait_until="domcontentloaded", timeout=15000)
        login_page.wait_for_timeout(800)
        results.append(
            save_png(
                Image.open(BytesIO(login_page.screenshot(full_page=False))),
                "P2-17-grafana-login.png",
                env,
            )
        )
        login_page.locator('input[name="user"]').fill(username)
        login_page.locator('input[name="password"]').fill(password)
        login_page.locator('button[type="submit"]').click()
        login_page.wait_for_url(lambda url: "/login" not in url, timeout=15000)

        found: set[str] = set()
        for dashboard in dashboards:
            title = dashboard["title"]
            filename = dashboard_file(title)
            if filename is None or filename in found:
                continue
            found.add(filename)
            url = f"{base}{dashboard['url']}?from=now-1h&to=now&timezone=UTC&theme=dark"
            try:
                results.append(capture_image(login_page, url, filename, env))
            except Exception as error:
                results.append(
                    CaptureResult(
                        filename,
                        "Failed",
                        f"Grafana dashboard capture failed: {type(error).__name__}",
                    )
                )
        for filename in DASHBOARD_FILES.values():
            if filename not in found:
                results.append(
                    skip(filename, "No matching dashboard was returned by the Grafana API")
                )

        results.append(capture_exemplar(login_page, base, env))
        results.append(capture_tempo_trace(login_page, base, env))
    except Exception as error:
        if not any(item.image == "P2-17-grafana-login.png" for item in results):
            results.append(
                CaptureResult(
                    "P2-17-grafana-login.png",
                    "Failed",
                    f"Grafana login capture failed: {type(error).__name__}",
                )
            )
        for name in DASHBOARD_FILES.values():
            if not any(item.image == name for item in results):
                results.append(
                    CaptureResult(
                        name,
                        "Failed",
                        (
                            "Grafana authentication or dashboard loading failed: "
                            f"{type(error).__name__}"
                        ),
                    )
                )
        if not any(item.image == "grafana-exemplar.png" for item in results):
            results.append(
                CaptureResult(
                    "grafana-exemplar.png",
                    "Failed",
                    f"Grafana Explore capture failed: {type(error).__name__}",
                )
            )
        if not any(item.image == "tempo-trace.png" for item in results):
            results.append(
                CaptureResult(
                    "tempo-trace.png",
                    "Failed",
                    f"Grafana trace capture failed: {type(error).__name__}",
                )
            )
    finally:
        context.close()
    return results


def capture_tempo_trace(page: object, base: str, env: dict[str, str]) -> CaptureResult:
    name = "tempo-trace.png"
    tempo = env.get("TEMPO_URL", "http://localhost:3200").rstrip("/")
    end = int(time.time())
    try:
        payload = fetch_json(
            f"{tempo}/api/search?" + urlencode({"limit": 1, "start": end - 3600, "end": end})
        )
        traces = payload.get("traces", [])
        if not traces:
            return skip(name, "Tempo returned no traces in the fixed one-hour range")
        trace_id = traces[0].get("traceID") or traces[0].get("traceId")
        if not trace_id:
            return skip(name, "Tempo search returned a trace without an ID")

        left = {
            "datasource": "tempo",
            "queries": [
                {
                    "refId": "A",
                    "queryType": "traceql",
                    "query": f'{{ trace:id = "{trace_id}" }}',
                }
            ],
            "range": {
                "from": "now-1h",
                "to": "now",
                "raw": {"from": "now-1h", "to": "now"},
            },
        }
        url = (
            f"{base}/explore?left="
            f"{quote(json.dumps(left, separators=(',', ':')))}&theme=dark"
        )
        return capture_image(page, url, name, env)
    except (requests.RequestException, ValueError, AttributeError):
        return skip(name, "Tempo search API is unavailable")
    except Exception as error:
        return CaptureResult(
            name,
            "Failed",
            f"Grafana trace capture failed: {type(error).__name__}",
        )


def capture_exemplar(page: object, base: str, env: dict[str, str]) -> CaptureResult:
    name = "grafana-exemplar.png"
    prometheus = env.get("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")
    end = int(time.time())
    query = "http_request_duration_seconds_bucket"
    try:
        payload = fetch_json(
            f"{prometheus}/api/v1/query_exemplars?"
            + urlencode({"query": query, "start": end - 3600, "end": end})
        )
        data = payload.get("data", [])
        if not data:
            return skip(name, "Prometheus returned no exemplars for the fixed one-hour range")
        explorer = {
            "datasource": "prometheus",
            "queries": [{"refId": "A", "expr": query, "exemplar": True}],
            "range": {"from": "now-1h", "to": "now", "raw": {"from": "now-1h", "to": "now"}},
        }
        url = f"{base}/explore?left={quote(json.dumps(explorer, separators=(',', ':')))}&theme=dark"
        return capture_image(page, url, name, env)
    except (requests.RequestException, ValueError, AttributeError):
        return skip(name, "Prometheus exemplar API is unavailable or has no matching data")


def capture_public_page(browser: object, url: str, name: str, env: dict[str, str]) -> CaptureResult:
    page = browser.new_page(viewport=VIEWPORT, color_scheme="dark")
    try:
        return capture_image(page, url, name, env)
    except Exception as error:
        return skip(
            name,
            f"Page is unavailable ({type(error).__name__}) at "
            f"{url.split('/', 3)[0]}//{url.split('/', 3)[2]}",
        )
    finally:
        page.close()


def capture_services(browser: object, env: dict[str, str]) -> list[CaptureResult]:
    targets = [
        ("prometheus-alert-rules.png", "http://localhost:9090/rules"),
        ("prometheus-targets-up.png", "http://localhost:9090/targets"),
        (
            "prometheus-container-cpu-metrics.png",
            "http://localhost:9090/graph?g0.expr=container_cpu_usage_seconds_total",
        ),
        ("alertmanager-group.png", "http://localhost:9093/#/alerts"),
    ]
    results = []
    for name, url in targets:
        result = capture_public_page(browser, url, name, env)
        results.append(result)
    name = "prometheus-cpu-alert-firing.png"
    page = browser.new_page(viewport=VIEWPORT, color_scheme="dark")
    try:
        page.goto("http://localhost:9090/alerts", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(800)
        if "apihighlatency" not in page.locator("body").inner_text().casefold():
            results.append(skip(name, "ApiHighLatency is not firing"))
        else:
            results.append(
                save_png(
                    Image.open(BytesIO(page.screenshot(full_page=False))),
                    name,
                    env,
                )
            )
    except Exception as error:
        results.append(
            skip(name, f"Prometheus alerts page is unavailable ({type(error).__name__})")
        )
    finally:
        page.close()
    return results


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        emit(
            [
                skip(name, "Install the pinned development requirements and Chromium browser")
                for name in [
                    *DASHBOARD_FILES.values(),
                    "P2-17-grafana-login.png",
                    "grafana-exemplar.png",
                    "prometheus-alert-rules.png",
                    "alertmanager-group.png",
                    "tempo-trace.png",
                ]
            ]
        )
        return

    env = read_env()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        results = capture_grafana(browser, env)
        results.extend(capture_services(browser, env))
        browser.close()
    emit(results)


if __name__ == "__main__":
    main()
