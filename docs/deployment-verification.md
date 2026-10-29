# Deployment verification

Date (UTC): 2026-10-29

| Check | Status | Result |
|---|---|---|
| HTTPS response | Passed | HTTP 302 |
| TLS version | Passed | TLS 1.3 only handshake succeeded |
| HTTP redirect | Passed | 301 to https://localhost/ |
| Header Strict-Transport-Security | Passed | Present |
| Header X-Content-Type-Options | Passed | Present |
| Header X-Frame-Options | Passed | Present |
| Header Referrer-Policy | Passed | Present |
| Header Permissions-Policy | Passed | Present |
| Port 9090 closed | Passed | Closed |
| Port 9093 closed | Passed | Closed |
| Port 3200 closed | Passed | Closed |
| Port 8000 closed | Passed | Closed |
| Port 8001 closed | Passed | Closed |
| Port 8090 closed | Passed | Closed |
| Port 8091 closed | Passed | Closed |
| Port 8092 closed | Passed | Closed |
| Port 9100 closed | Passed | Closed |
| Port 8085 closed | Passed | Closed |
| Port 8474 closed | Passed | Closed |
| Port 4317 closed | Passed | Closed |
| Port 4318 closed | Passed | Closed |
| Port 3000 closed | Passed | Closed |
| Chaos path blocked | Passed | HTTP 404 |
| Admin path blocked | Passed | HTTP 404 |
| Grafana authentication required | Passed | HTTP 401 |
