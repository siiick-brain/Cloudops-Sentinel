import logging
import os
import random
import time
from typing import Annotated

import requests
from fastapi import Depends, FastAPI, Header, HTTPException, Response
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from pydantic import BaseModel

from app.observability import instrument

app = FastAPI(title="CloudOps Sentinel orders API")
logger = logging.getLogger("orders")
chaos_latency = 0.0
chaos_error_rate = 0.0
RequestsInstrumentor().instrument()


class ChaosSettings(BaseModel):
    latency_seconds: float = 0
    error_rate: float = 0


def check_chaos_token(
    token: Annotated[str | None, Header(alias="X-Chaos-Token")] = None,
) -> None:
    expected = os.getenv("CHAOS_TOKEN", "local-demo-token")
    if token != expected:
        raise HTTPException(status_code=401, detail="invalid chaos token")


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def ready(response: Response) -> dict[str, str]:
    if os.getenv("API_UNREADY") == "1":
        response.status_code = 503
        return {"status": "not_ready"}
    return {"status": "ready"}


@app.get("/orders/{sku}")
def order(sku: str) -> dict[str, object]:
    if chaos_latency > 0:
        time.sleep(chaos_latency)
    if random.random() < chaos_error_rate:
        logger.error("request fault injected")
        raise HTTPException(status_code=503, detail="injected failure")
    inventory_url = os.getenv("INVENTORY_URL", "http://localhost:8001")
    try:
        response = requests.get(f"{inventory_url}/inventory/{sku}", timeout=3)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("inventory request failed")
        raise HTTPException(status_code=503, detail="inventory unavailable") from exc
    logger.info("order checked for sku=%s", sku)
    return {"order_status": "accepted", "inventory": response.json()}


@app.post("/chaos", dependencies=[Depends(check_chaos_token)])
def set_chaos(settings: ChaosSettings) -> dict[str, float]:
    global chaos_latency, chaos_error_rate
    if not 0 <= settings.latency_seconds <= 10 or not 0 <= settings.error_rate <= 1:
        raise HTTPException(status_code=422, detail="chaos values are out of range")
    chaos_latency = settings.latency_seconds
    chaos_error_rate = settings.error_rate
    logger.warning(
        "chaos settings changed latency_seconds=%s error_rate=%s",
        chaos_latency,
        chaos_error_rate,
    )
    return {"latency_seconds": chaos_latency, "error_rate": chaos_error_rate}


@app.delete("/chaos", dependencies=[Depends(check_chaos_token)])
def clear_chaos() -> dict[str, str]:
    global chaos_latency, chaos_error_rate
    chaos_latency = 0
    chaos_error_rate = 0
    return {"status": "cleared"}


instrument(app, "api")
