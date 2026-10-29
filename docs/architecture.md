# Architecture

CloudOps Sentinel runs as Docker Compose services on one local host. Development Compose publishes service ports for local testing. Production-style Compose publishes only Caddy on loopback.

## Components and ports

| Compose service | Role | Development host port | Production-style host access |
|---|---|---:|---|
| `caddy` | Local TLS termination, HTTP redirect and Grafana reverse proxy | Not enabled | 127.0.0.1:80 and 127.0.0.1:443 |
| `api` | Orders API, request metrics, traces and chaos control | 8000 | Internal only |
| `backend` | Inventory API, request metrics and traces | 8001 | Internal only |
| `loadgen` | Sends steady requests to the orders API | None | Internal only |
| `prometheus` | Scrapes metrics and evaluates alert and SLO rules | 9090 | Internal only |
| `alertmanager` | Groups, inhibits and routes firing and resolved alerts | 9093 | Internal only |
| `grafana` | Dashboards and trace exploration | 3000 | Through Caddy |
| `node-exporter` | Linux host metrics | 9100 | Internal only |
| `cadvisor` | Container resource metrics | 8085 | Internal only |
| `docker-exporter` | Docker Engine metrics | Internal port 9713 | Internal only |
| `otel-collector` | Receives OTLP spans and exports traces and span metrics | 4317 and 4318 | Internal only |
| `tempo` | Trace storage and query API | 3200 | Internal only |
| `toxiproxy` | Fault injection between the API and inventory | 8474 | Internal only |
| `alert-router` | Authenticated webhook and Slack and Jira delivery | 8090 | Internal only |
| `mock-slack` | Local Slack webhook receiver | 8091 | Internal only |
| `mock-jira` | Local Jira issue API receiver | 8092 | Internal only |
| `chaos-tools` | Bounded CPU, memory and disk workloads | None | Not included |

Development ports are declared in [docker-compose.yml](../docker-compose.yml). Production-style port overrides are in [compose.prod.yml](../compose.prod.yml).

## Data flows

- The load generator calls the orders API. The API calls inventory through Toxiproxy.
- The API and inventory expose Prometheus request counters and latency histograms. Prometheus scrapes those services and the router, mocks, Grafana, Alertmanager, Tempo, the collector, node-exporter, cAdvisor and Docker exporter.
- The API and inventory export spans over OTLP to the collector. The collector exports traces to Tempo and span metrics to Prometheus.
- The API histogram includes trace exemplars. Grafana queries Prometheus and Tempo.
- Prometheus evaluates platform and SLO rules. Alertmanager groups and routes notifications to the router.
- The router delivers Slack messages and creates, deduplicates, comments on or resolves Jira issues. Local runs use mock receivers by default.
- Application logs are written to container stdout and stderr. Application log records include an active trace ID when a span exists. Docker captures container output.

## Trust boundary

The Docker Compose network is local to the host. In the production-style deployment, Caddy binds to loopback, accepts TLS 1.3, redirects HTTP to HTTPS and proxies Grafana only. It does not proxy chaos or admin paths. Application, monitoring, router and mock ports remain unpublished. Development Compose publishes service ports for local testing and is not the restricted deployment.

## Failure modes

| Failure | Detection or effect |
|---|---|
| API returns server errors or exceeds its latency objective | Prometheus evaluates API golden-signal and burn-rate rules |
| Inventory is slow or unavailable | API latency rises or the API returns a server error |
| A monitored target stops responding | Prometheus target alerts link to the relevant runbook |
| Docker Desktop uses the containerd image store | cAdvisor v0.49.2 reported missing layer IDs. The recorded cAdvisor v0.60.6 check returned named CPU and memory samples with the existing mounts |
| Mock service restarts | In-memory Slack and Jira mock state resets |
| Local host or Docker Engine stops | All local services become unavailable. The deployment has no high availability |
| Collector or Tempo is unavailable | New traces may not be stored. Request metrics remain a separate signal |

The objectives and budget policy are in [slo.md](slo.md). Alert definitions link to [runbooks](runbooks/).
