# Architecture

CloudOps Sentinel runs as Docker Compose services on one local host. The development stack publishes service ports for local inspection. The production-style configuration publishes only Caddy on localhost ports 80 and 443.

## Components and ports

| Component | Role | Development host port | Production-style host access |
|---|---|---:|---|
| Caddy | Local TLS, redirect and Grafana reverse proxy | Not enabled | 80 and 443 on localhost |
| API | Orders endpoint, request metrics, traces and chaos control | 8000 | Internal only |
| Backend | Inventory endpoint and traces | 8001 | Internal only |
| Load generator | Sends steady API requests | None | Internal only |
| Prometheus | Scrapes targets and evaluates rules | 9090 | Internal only |
| Alertmanager | Groups and routes firing or resolved alerts | 9093 | Internal only |
| Grafana | Dashboards and trace exploration | 3000 | Through Caddy |
| Node exporter | Host metrics from the Linux environment | 9100 | Internal only |
| cAdvisor | Container metrics | 8085 | Internal only |
| Docker exporter | Docker engine metrics | Internal port 9713 | Internal only |
| OpenTelemetry Collector | Receives OTLP spans and exports span metrics | 4317 and 4318 | Internal only |
| Tempo | Trace storage and query API | 3200 | Internal only |
| Toxiproxy | Fault injection between the API and inventory | 8474 | Internal only |
| Alert router | Authenticated webhook, Slack and Jira delivery | 8090 | Internal only |
| Mock Slack | Local incoming webhook receiver | 8091 | Internal only |
| Mock Jira | Local issue API receiver | 8092 | Internal only |
| Chaos tools | Bounded CPU, memory and disk workloads | None | Not included in production-style Compose |

Development ports are declared in [docker-compose.yml](../docker-compose.yml). Production-style port overrides are in [compose.prod.yml](../compose.prod.yml).

## Data flows

- The load generator calls the orders API. The API calls inventory through Toxiproxy.
- The API and inventory expose Prometheus counters and latency histograms. Prometheus also scrapes the router, mocks, Grafana, Tempo, the collector, node exporter, cAdvisor and Docker exporter.
- The API and inventory export spans over OTLP to the collector. The collector sends spans to Tempo and span-derived metrics to Prometheus.
- The API histogram includes trace exemplars. Grafana queries Prometheus and Tempo.
- Prometheus evaluates platform and SLO rules. Alertmanager groups, inhibits and routes notifications to the router.
- The router sends Slack messages and creates, deduplicates, comments on or resolves Jira issues. Local runs use the mock receivers by default.
- Application logs are JSON on stdout and include the active trace ID when a span exists. Docker captures the container output.

## Trust boundary

The production-style local deployment binds Caddy to loopback. Caddy accepts TLS 1.3, redirects HTTP to HTTPS and proxies Grafana only. It does not proxy chaos or admin paths. Monitoring, application, router and mock ports are unpublished in this configuration. The development Compose file intentionally publishes service ports and is for local testing.

## Failure modes

| Failure | Detection or effect |
|---|---|
| API returns server errors or exceeds the latency objective | API golden-signal and burn-rate alerts evaluate the Prometheus request metrics |
| Inventory is slow or unavailable | API request latency rises or the API returns a server error |
| A monitored target stops responding | Prometheus target alerts and the corresponding runbook identify the target |
| Docker Desktop uses the containerd image store | Older cAdvisor v0.49.2 reports missing layer IDs. The configured v0.60.6 returned named CPU and memory samples in the recorded local check |
| Mock service restarts | In-memory Slack and Jira mock state resets |
| Local host or Docker Engine stops | All local services become unavailable. This deployment has no high availability |
| Trace collector or Tempo is unavailable | New traces may not be stored. API request metrics remain a separate signal |

The SLO targets and budget policy are in [slo.md](slo.md). Alert definitions link to individual [runbooks](runbooks/).
