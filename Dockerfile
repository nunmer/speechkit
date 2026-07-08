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
    mkdir -p /app/uploads && \
    chown appuser /app/uploads

COPY --from=builder /install /usr/local
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini ./
COPY scripts/ scripts/
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser

EXPOSE 8000

ENV PYTHONPATH=/app

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fs http://localhost:8000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["api"]
