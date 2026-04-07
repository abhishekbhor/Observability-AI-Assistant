from __future__ import annotations

from app.models.schemas import InvestigationRequest, InvestigationResponse
from app.services.anomaly import AnomalyService
from app.services.llm import LLMService
from app.services.retrieval import RetrievalService
from app.services.root_cause import RootCauseService
from app.services.telemetry_store import TelemetryStore


class ObservabilityAssistant:
    def __init__(
        self,
        store: TelemetryStore,
        retrieval_service: RetrievalService,
        anomaly_service: AnomalyService,
        root_cause_service: RootCauseService,
        llm_service: LLMService,
    ) -> None:
        self.store = store
        self.retrieval_service = retrieval_service
        self.anomaly_service = anomaly_service
        self.root_cause_service = root_cause_service
        self.llm_service = llm_service

    def investigate(self, request: InvestigationRequest) -> InvestigationResponse:
        snapshot = self.store.query(
            services=request.services,
            environment=request.environment,
            lookback_minutes=request.lookback_minutes,
        )
        anomalies = self.anomaly_service.detect(snapshot.metrics)
        documents = self.retrieval_service.build_documents(snapshot.logs, snapshot.metrics, snapshot.traces)
        retrieved = self.retrieval_service.top_k(request.question, documents, k=request.top_k)
        likely_root_causes = self.root_cause_service.infer(snapshot.logs, snapshot.traces, anomalies)
        evidence = [
            {
                "doc_id": d.doc_id,
                "source_type": d.source_type,
                "service": d.service,
                "text": d.text,
                "metadata": d.metadata,
            }
            for d in retrieved
        ]
        summary = self.llm_service.summarize(
            question=request.question,
            likely_root_causes=likely_root_causes,
            anomalies=anomalies,
            evidence=evidence,
        )
        service_map = self.store.service_map(snapshot.traces)
        return InvestigationResponse(
            question=request.question,
            summary=summary,
            likely_root_causes=likely_root_causes,
            anomalies=anomalies,
            evidence=evidence,
            service_map=service_map,
        )
