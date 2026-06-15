import os

from prometheus_client import (
    Counter, Histogram,
    CollectorRegistry,
    generate_latest, CONTENT_TYPE_LATEST,
    REGISTRY,
)
from prometheus_client.multiprocess import MultiProcessCollector


def make_registry() -> CollectorRegistry:
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
        return registry
    return REGISTRY


REQUEST_COUNT = Counter(
    "speech_requests_total",
    "Total requests by endpoint and status",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "speech_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
)

ENGINE_ERRORS = Counter(
    "speech_engine_errors_total",
    "Engine errors by engine and operation",
    ["engine", "operation"],
)

AUDIO_DURATION = Histogram(
    "speech_audio_duration_seconds",
    "Audio duration processed",
    ["operation", "engine"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)
