import logging
import os
import time

from fastapi import FastAPI, HTTPException, Response

from app.observability import instrument

app = FastAPI(title="CloudOps Sentinel inventory service")
logger = logging.getLogger("inventory")
fail_rate = 0.0
delay_seconds = 0.0


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def ready(response: Response) -> dict[str, str]:
    if os.getenv("BACKEND_UNREADY") == "1":
        response.status_code = 503
        return {"status": "not_ready"}
    return {"status": "ready"}


@app.get("/inventory/{sku}")
def inventory(sku: str) -> dict[str, object]:
    if delay_seconds:
        time.sleep(delay_seconds)
    if fail_rate >= 1:
        logger.warning("inventory fault injected")
        raise HTTPException(status_code=503, detail="inventory unavailable")
    return {"sku": sku, "available": True, "quantity": 42}


instrument(app, "inventory")
