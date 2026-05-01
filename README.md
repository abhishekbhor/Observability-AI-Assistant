# Observability AI Assistant
## Observability AI Assistant

An AI-powered observability system that investigates production incidents by correlating logs, metrics, and traces to identify likely root causes.

Unlike traditional dashboards or RAG-based assistants, this system performs structured incident analysis — detecting anomalies, mapping service dependencies, and generating root-cause hypotheses from telemetry data.

Built as an end-to-end FastAPI application, it simulates how modern AI systems can assist SREs and engineers in debugging distributed systems.

This Assistant includes:
- telemetry ingestion APIs for logs, metrics, and traces
- correlation engine across services and time windows
- anomaly detection on time-series metrics
- root-cause hypothesis generation
- natural-language Q&A over recent telemetry context
- optional distributed GPU embedding pipeline with CPU fallback
- clean architecture and small, understandable modules

## Why this is different from a standard RAG assistant

A normal RAG assistant answers questions from static documents.

This project is different because it reasons over **live operational signals**:
- logs with severity, service, environment, incident IDs
- traces with latency and error spans
- metrics with time windows and z-score anomaly detection
- service dependency correlation
- incident-focused summaries instead of generic retrieval

## Architecture

```text
Client / Dashboard / CLI
          |
          v
      FastAPI API
          |
          +-------------------------------+
          |                               |
          v                               v
Telemetry Store                    Assistant Services
(logs / traces / metrics)          - context builder
                                   - retrieval
                                   - anomaly detection
                                   - root-cause hypotheses
                                   - summarization
          |
          v
Parallel Embedding Engine
(CPU fallback, multi-process, optional multi-GPU sharding)
```

## Project structure

```text
observ_ai_assistant/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   └── config.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── anomaly.py
│   │   ├── assistant.py
│   │   ├── embedding.py
│   │   ├── llm.py
│   │   ├── retrieval.py
│   │   ├── root_cause.py
│   │   └── telemetry_store.py
│   ├── utils/
│   │   └── time.py
│   └── main.py
├── tests/
│   └── test_assistant.py
├── requirements.txt
└── README.md
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/docs`

## I Example workflow

### 1) Ingest telemetry

```bash
curl -X POST http://127.0.0.1:8000/telemetry/batch \
  -H "Content-Type: application/json" \
  -d @sample_telemetry.json
```

### 2) Ask for an investigation summary

```bash
curl -X POST http://127.0.0.1:8000/assistant/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why is checkout failing for production users?",
    "services": ["checkout-service", "payment-service"],
    "environment": "prod",
    "lookback_minutes": 90,
    "top_k": 8
  }'
```
## II Example workflow
### sample_telemetry_postgres_outage.json for payments/postgres
- This one is tuned for a payments -> postgres failure scenario:

- repeated DB timeout logs
- latency spike
- error-rate spike
- failed POST /charge traces
- dependency mapping to postgres

Investigation body:
```bash
{
  "question": "Why is the payments service failing?",
  "services": ["payments"],
  "environment": "prod",
  "lookback_minutes": 300,
  "top_k": 8
}
```

## Optional environment variables

```bash
export OBS_LLM_MODE=heuristic
export OBS_EMBEDDING_DIM=64
export OBS_ENABLE_GPU=true
export OBS_GPU_WORKERS=2
export OBS_DEFAULT_LOOKBACK_MINUTES=120
```

Notes:
- `heuristic` mode is included, so the app runs without an external LLM.
- One can later swap in OpenAI or another provider inside `app/services/llm.py`.
- GPU code is optional and safely falls back to CPU when CUDA is not available.

## Highlights

- built an observability-native AI assistant instead of a document chatbot
- modeled logs, traces, and metrics as separate but correlated signals
- added anomaly scoring and service dependency reasoning
- designed a distributed embedding path that can shard telemetry batches across GPUs
- kept the system production-shaped: API layer, domain models, services, and tests



# Demo Outcome
### Example Investigation (Real Output)

Simulated incident: Payments service failure in production.

Input question:
> Why is the payments service failing?

System output (abridged):

- Identified `payments` as the primary failing service
- Detected repeated high-severity logs:
  - "Database connection timeout"
- Correlated failed traces on operation:
  - `POST /charge`
- Mapped downstream dependency:
  - `payments → postgres`
- Observed latency spike:
  - from ~200ms → 1450ms

### Likely root cause

- Database connectivity failure between `payments` and `postgres`
- Timeouts during charge processing leading to cascading latency and errors

This demonstrates:
- multi-signal correlation (logs + traces + metrics)
- dependency-aware reasoning
- automated root-cause hypothesis generation
