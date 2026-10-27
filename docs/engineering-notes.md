# Engineering notes

## Local service topology

The platform uses separate FastAPI services for orders, inventory and alert routing. The orders API calls inventory through Toxiproxy so the chaos runner can exercise a real service boundary. Prometheus, Alertmanager, Grafana, Tempo and the OpenTelemetry Collector run in Compose.

The production-style Compose file reuses service definitions and removes their published host ports. Caddy binds to localhost and proxies Grafana only. The development Compose file keeps ports available for local inspection.

## Metrics, traces and logs

The services expose Prometheus request counters and histograms. The API and inventory emit OpenTelemetry spans. The collector exports traces to Tempo and span metrics to Prometheus. Structured application logs go to stdout and include the trace ID when one is active.

Dashboards are generated in Python with the Grafana Foundation SDK. The CI workflow regenerates dashboards and SLO rules then checks for drift.

## SLO implementation

The source SLO spec defines availability at 99.5 percent and latency at 95 percent below 300 ms over 30 days. Handwritten Prometheus recording rules compute the rolling ratios and remaining budgets. Multi-window burn rules use the defined objectives. The [SLO policy](slo.md) describes how to respond when a budget is exhausted.

## cAdvisor layer error

The recorded Docker host reported the `overlayfs` driver and the `io.containerd.snapshotter.v1` driver status. With the containerd image store active, cAdvisor v0.49.2 repeatedly failed to identify the read-write layer ID and produced no named per-container CPU samples.

The image pin was upgraded to cAdvisor v0.60.6 without changing its mounts. An isolated run and the local production-style stack returned named CPU and memory metrics for the API container. The Docker storage check still reports `overlayfs` and asks the operator to confirm metrics before relying on resource alerts. The CPU, memory and disk alert scenarios remain unverified.

The manual Docker Desktop workaround is to turn off **Use containerd for pulling and storing images**. On Docker Engine, set `features.containerd-snapshotter` to `false` in the daemon configuration. Do not change cAdvisor mounts based only on the warning.

## Recorded verification

The recorded unit test run on 2026-10-28 passed 20 tests with 83.92 percent coverage. The local deployment check passed 25 checks on 2026-10-27. Four local mock-backed chaos scenarios recorded firing alerts and Slack and Jira confirmation. The CPU stress, memory pressure and disk fill runs failed to confirm their expected alerts.

On 2026-10-27, a manual real integration exercise logged successful Jira requests and Slack HTTP 200 responses. The complete live end-to-end record is unavailable. The project does not treat the exercise as full live verification.

## Failures and corrections

- The earlier cAdvisor image produced layer-ID errors with the Docker Desktop containerd image store. Version 0.60.6 exposed named metrics with the existing mounts.
- The example environment file contained an external Jira URL while selecting mocks. Mock mode now forces local receiver addresses and the Jira mock supports the v3 search path used by the router. Regression tests cover both behaviors.
- A first curl-based deployment check requested an unsupported curl output variable for the TLS version. The shell check now verifies the handshake by allowing TLS 1.3 only.
- Local test commands must use the project virtual environment. The global pytest launcher was incompatible with its installed package, while the project environment passed the suite.
- Full workspace secret scans include ignored local files. Report those findings separately from scans of committed source.

See the [verification scorecard](../artifacts/scorecard.md) for current statuses.
