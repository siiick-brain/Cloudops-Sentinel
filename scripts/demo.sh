#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
printf '%s\n' "1/6 Starting services"
docker compose up -d --build
printf '%s\n' "2/6 Waiting for service and target readiness"
python scripts/wait_for_stack.py
printf '%s\n' "3/6 Sending service traffic"
curl --fail --silent http://localhost:8000/orders/demo-sku >/dev/null
printf '%s\n' "4/6 Checking the cross-service trace"
python scripts/check_trace.py
printf '%s\n' "5/6 Triggering a latency chaos scenario"
python chaos/run.py latency
printf '%s\n' "6/6 Checking stack health"
docker compose ps
