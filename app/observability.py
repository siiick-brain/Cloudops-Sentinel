import json
import logging
import os
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests served",
    ["service", "method", "route", "status"],
)
LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["service", "route"],
    buckets=(0.05, 0.1, 0.2, 0.3, 0.5, 1, 2, 5),
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        span_context = trace.get_current_span().get_span_context()
        trace_id = f"{span_context.trace_id:032x}" if span_context.is_valid else ""
        return json.dumps(
            {
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "trace_id": trace_id,
            },
            separators=(",", ":"),
        )


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def configure_tracing(service_name: str) -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)


def instrument(app: FastAPI, service: str) -> None:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from prometheus_client import make_asgi_app

    configure_logging()
    configure_tracing(service)
    FastAPIInstrumentor.instrument_app(app)
    app.mount("/metrics", make_asgi_app())

    @app.middleware("http")
    async def record_metrics(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)
        start = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        route_name = getattr(route, "path", request.url.path)
        span_context = trace.get_current_span().get_span_context()
        exemplar = {"trace_id": f"{span_context.trace_id:032x}"} if span_context.is_valid else None
        LATENCY.labels(service, route_name).observe(time.perf_counter() - start, exemplar=exemplar)
        REQUESTS.labels(service, request.method, route_name, str(response.status_code)).inc()
        return response
