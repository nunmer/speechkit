import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY  # noqa: F401 — side-effect registration

logger = logging.getLogger("speech_service.request")

_SKIP_PATHS = {"/health", "/metrics"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        path = request.url.path
        if path not in _SKIP_PATHS:
            logger.info(
                "%s %s %d %.0fms",
                request.method, path, response.status_code, duration * 1000,
                extra={"request_id": request_id},
            )
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=path,
                status_code=response.status_code,
            ).inc()
            REQUEST_LATENCY.labels(method=request.method, endpoint=path).observe(duration)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration * 1000:.1f}"
        return response
