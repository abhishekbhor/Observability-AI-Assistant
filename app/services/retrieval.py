from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import LogEvent, MetricPoint, TraceSpan
from app.services.embedding import EmbeddingService


@dataclass
class EvidenceDocument:
    doc_id: str
    source_type: str
    service: str
    text: str
    metadata: dict


class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service

    def build_documents(
        self, logs: list[LogEvent], metrics: list[MetricPoint], traces: list[TraceSpan]
    ) -> list[EvidenceDocument]:
        docs: list[EvidenceDocument] = []

        for i, log in enumerate(logs):
            docs.append(
                EvidenceDocument(
                    doc_id=f"log-{i}",
                    source_type="log",
                    service=log.service,
                    text=(
                        f"[{log.severity}] service={log.service} env={log.environment} "
                        f"message={log.message} trace_id={log.trace_id or 'none'}"
                    ),
                    metadata={
                        "timestamp": log.timestamp.isoformat(),
                        "incident_id": log.incident_id,
                        "host": log.host,
                    },
                )
            )

        for i, metric in enumerate(metrics):
            docs.append(
                EvidenceDocument(
                    doc_id=f"metric-{i}",
                    source_type="metric",
                    service=metric.service,
                    text=(
                        f"metric service={metric.service} name={metric.metric_name} "
                        f"value={metric.value} unit={metric.unit or 'none'}"
                    ),
                    metadata={
                        "timestamp": metric.timestamp.isoformat(),
                        "metric_name": metric.metric_name,
                        "value": metric.value,
                    },
                )
            )

        for i, trace in enumerate(traces):
            docs.append(
                EvidenceDocument(
                    doc_id=f"trace-{i}",
                    source_type="trace",
                    service=trace.service,
                    text=(
                        f"trace service={trace.service} operation={trace.operation} status={trace.status} "
                        f"duration_ms={trace.duration_ms} downstream={trace.downstream_service or 'none'} "
                        f"error={trace.error_message or 'none'}"
                    ),
                    metadata={
                        "timestamp": trace.timestamp.isoformat(),
                        "trace_id": trace.trace_id,
                        "span_id": trace.span_id,
                    },
                )
            )

        return docs

    def top_k(self, question: str, documents: list[EvidenceDocument], k: int = 8) -> list[EvidenceDocument]:
        if not documents:
            return []
        query_vec = self.embedding_service.embed_text(question)
        doc_matrix = self.embedding_service.embed_batch([doc.text for doc in documents])
        scores = self.embedding_service.cosine_similarity(query_vec, doc_matrix)
        ranked = sorted(zip(documents, scores), key=lambda x: float(x[1]), reverse=True)
        return [doc for doc, _ in ranked[:k]]
