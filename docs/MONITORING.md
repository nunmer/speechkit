# Monitoring

## Metrics

The API exposes Prometheus metrics at `GET /metrics`.

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `speech_requests_total` | counter | method, endpoint, status_code | HTTP requests |
| `speech_request_duration_seconds` | histogram | method, endpoint | Request latency |
| `speech_engine_errors_total` | counter | engine, operation | Upstream engine failures |
| `speech_audio_duration_seconds` | histogram | operation, engine | Audio length processed |
| `speech_jobs_total` | counter | kind, engine, status | Async STT jobs by terminal status |
| `speech_job_duration_seconds` | histogram | kind, engine | Engine processing time per job |
| `speech_dedup_hits_total` | counter | kind | Requests served from cache/dedup |

Under Gunicorn/Uvicorn multi-worker mode, set `PROMETHEUS_MULTIPROC_DIR` so
counters aggregate across workers (already set in the image).

## Stack

`docker compose up` starts Prometheus (`:9090`) and Grafana (`:3000`).

- Prometheus scrapes the API and loads alert rules from `monitoring/alerts.yml`.
- Grafana auto-provisions the Prometheus datasource and the **Speech Service**
  dashboard (`monitoring/grafana/dashboards/speech-service.json`).

## Alerts (`monitoring/alerts.yml`)

| Alert | Fires when |
|---|---|
| `HighRequestErrorRate` | >5% of requests are 5xx over 5m |
| `EngineErrorsSpike` | Upstream engine error rate elevated for 10m |
| `STTJobFailureRate` | >10% of async jobs failing over 10m |
| `SlowRequests` | p95 request latency > 30s (consider the async endpoints) |

## Tracing

Each request carries an `X-Request-ID` (generated if absent). It is logged on
every request and stored on the async job record (`speech_jobs.request_id`), so a
client request can be correlated with its worker-side processing logs.
