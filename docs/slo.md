# API service level objectives

The API objectives use a rolling 30-day window.

| Objective | Good event | Total event | Target | Budget |
|---|---|---|---:|---:|
| Availability | Response without a 5xx status | Completed API request | 99.5 percent | 0.5 percent |
| Latency | Request completes below 300 ms | Completed API request | 95 percent | 5 percent |

The source specification is [monitoring/prometheus/slo.yml](../monitoring/prometheus/slo.yml). Prometheus records 30-day objective ratios and short-window measurements and applies multi-window burn alerts. The rolling 30-day values need 30 days of retained request data before the complete window is available.

## Error budget policy

The availability budget is 0.5 percent of requests in the rolling window. If the remaining budget reaches zero, pause risky changes, review the error sources and prioritize reliability work. If the budget is above zero, change risk still depends on the incident record and observed burn rate.

The latency budget is 5 percent of requests at or above 300 ms. Investigate sustained burn even when availability remains within target. The two objectives are independent.

The demo has limited retention and an in-memory local integration path. Do not treat this short-lived dataset as a contractual SLO report.
