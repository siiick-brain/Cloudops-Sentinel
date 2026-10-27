#!/usr/bin/env bash
set -euo pipefail

fail() {
    printf 'Failed: %s\n' "$1" >&2
    exit 1
}

https_result=$(curl --silent --show-error --insecure --tlsv1.3 --tls-max 1.3 \
    --max-time 10 --output /dev/null --write-out '%{http_code}' https://localhost/)
https_code=$https_result
[[ "$https_code" =~ ^[23][0-9][0-9]$ ]] || fail "HTTPS returned HTTP $https_code"
printf 'Passed: HTTPS HTTP %s with a TLS 1.3 only handshake\n' "$https_code"

http_result=$(curl --silent --show-error --max-time 10 --output /dev/null \
    --write-out '%{http_code}|%{redirect_url}' http://localhost/)
http_code=${http_result%%|*}
redirect_url=${http_result#*|}
[[ "$http_code" == "301" || "$http_code" == "308" ]] || fail "HTTP returned $http_code"
[[ "$redirect_url" == https://localhost/* ]] || fail "HTTP redirect target is $redirect_url"
printf 'Passed: HTTP redirects to %s\n' "$redirect_url"

headers=$(curl --silent --show-error --insecure --max-time 10 --dump-header - \
    --output /dev/null https://localhost/)
for header in Strict-Transport-Security X-Content-Type-Options X-Frame-Options Referrer-Policy Permissions-Policy; do
    printf '%s\n' "$headers" | grep -qi "^${header}: " || fail "Missing security header $header"
    printf 'Passed: %s present\n' "$header"
done

for port in 9090 9093 3200 8000 8001 8090 8091 8092 9100 8085 8474 4317 4318 3000; do
    if curl --silent --show-error --connect-timeout 2 --max-time 3 \
        "http://127.0.0.1:${port}/" --output /dev/null; then
        fail "Internal port $port accepts a host connection"
    fi
    printf 'Passed: port %s is closed\n' "$port"
done

chaos_code=$(curl --silent --show-error --insecure --max-time 10 --output /dev/null \
    --write-out '%{http_code}' https://localhost/chaos)
[[ "$chaos_code" == "404" ]] || fail "Chaos path returned HTTP $chaos_code"
printf 'Passed: /chaos returns HTTP 404\n'

admin_code=$(curl --silent --show-error --insecure --max-time 10 --output /dev/null \
    --write-out '%{http_code}' https://localhost/admin)
[[ "$admin_code" == "404" ]] || fail "Admin path returned HTTP $admin_code"
printf 'Passed: /admin returns HTTP 404\n'

grafana_code=$(curl --silent --show-error --insecure --max-time 10 --output /dev/null \
    --write-out '%{http_code}' https://localhost/api/user)
[[ "$grafana_code" == "401" ]] || fail "Grafana API returned HTTP $grafana_code without credentials"
printf 'Passed: Grafana API requires authentication\n'
