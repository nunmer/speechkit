FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libsndfile1 curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -r -u 1001 -s /bin/false appuser && \
    mkdir -p /tmp/prometheus_multiproc && \
    chown appuser /tmp/prometheus_multiproc

COPY --from=builder /install /usr/local
COPY app/ app/
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser

EXPOSE 8000

ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fs http://localhost:8000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
