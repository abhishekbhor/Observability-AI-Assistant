from datetime import timedelta

from app.models.schemas import InvestigationRequest, LogEvent, MetricPoint, TelemetryBatch, TraceSpan
from app.services.anomaly import AnomalyService
from app.services.assistant import ObservabilityAssistant
from app.services.embedding import EmbeddingService
from app.services.llm import LLMService
from app.services.retrieval import RetrievalService
from app.services.root_cause import RootCauseService
from app.services.telemetry_store import TelemetryStore
from app.utils.time import utc_now


def build_assistant() -> tuple[ObservabilityAssistant, TelemetryStore]:
    store = TelemetryStore()
    assistant = ObservabilityAssistant(
        store=store,
        retrieval_service=RetrievalService(EmbeddingService(dim=32)),
        anomaly_service=AnomalyService(),
        root_cause_service=RootCauseService(),
        llm_service=LLMService(),
    )
    return assistant, store


def test_investigation_returns_root_cause_and_evidence() -> None:
    assistant, store = build_assistant()
    now = utc_now()

    batch = TelemetryBatch(
        logs=[
            LogEvent(
                timestamp=now - timedelta(minutes=10),
                service="checkout-service",
                environment="prod",
                severity="ERROR",
                message="payment authorization failed",
                trace_id="trace-1",
            ),
            LogEvent(
                timestamp=now - timedelta(minutes=8),
                service="checkout-service",
                environment="prod",
                severity="CRITICAL",
                message="payment authorization failed",
                trace_id="trace-2",
            ),
        ],
        metrics=[
            MetricPoint(timestamp=now - timedelta(minutes=12), service="checkout-service", metric_name="error_rate", value=0.02),
            MetricPoint(timestamp=now - timedelta(minutes=9), service="checkout-service", metric_name="error_rate", value=0.03),
            MetricPoint(timestamp=now - timedelta(minutes=5), service="checkout-service", metric_name="error_rate", value=0.25),
        ],
        traces=[
            TraceSpan(
                timestamp=now - timedelta(minutes=7),
                service="checkout-service",
                environment="prod",
                trace_id="trace-1",
                span_id="span-1",
                operation="POST /checkout",
                duration_ms=2130,
                status="error",
                error_message="downstream payment timeout",
                downstream_service="payment-service",
            )
        ],
    )
    store.ingest(batch)

    response = assistant.investigate(
        InvestigationRequest(
            question="Why is checkout failing?",
            services=["checkout-service"],
            environment="prod",
            lookback_minutes=60,
            top_k=5,
        )
    )

    assert response.likely_root_causes
    assert response.evidence
    assert any("checkout-service" in cause for cause in response.likely_root_causes)
