import sys
import time
from urllib.parse import quote

import requests

tempo = "http://localhost:3200"
deadline = time.monotonic() + 90
while time.monotonic() < deadline:
    end = int(time.time())
    result = requests.get(
        f"{tempo}/api/search",
        params={
            "tags": "service.name=api",
            "limit": 20,
            "start": end - 120,
            "end": end,
        },
        timeout=5,
    )
    result.raise_for_status()
    for candidate in result.json().get("traces", []):
        trace_id = candidate.get("traceID", "")
        if not trace_id:
            continue
        trace = requests.get(f"{tempo}/api/traces/{quote(trace_id)}", timeout=10)
        trace.raise_for_status()
        span_names = set()
        for batch in trace.json().get("batches", []):
            attributes = batch.get("resource", {}).get("attributes", [])
            for attribute in attributes:
                if attribute.get("key") == "service.name":
                    span_names.add(attribute.get("value", {}).get("stringValue"))
        if {"api", "inventory"}.issubset(span_names):
            print(f"Trace verified: {trace_id} includes api and inventory spans.")
            raise SystemExit(0)
    time.sleep(2)
print("No API trace with both api and inventory spans was returned by Tempo.", file=sys.stderr)
raise SystemExit(1)
