from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.services.anomaly import AnomalyService
from app.services.assistant import ObservabilityAssistant
from app.services.embedding import EmbeddingService
from app.services.llm import LLMService
from app.services.retrieval import RetrievalService
from app.services.root_cause import RootCauseService
from app.services.telemetry_store import TelemetryStore

store = TelemetryStore()
embedding_service = EmbeddingService()
retrieval_service = RetrievalService(embedding_service=embedding_service)
anomaly_service = AnomalyService()
root_cause_service = RootCauseService()
llm_service = LLMService()
assistant = ObservabilityAssistant(
    store=store,
    retrieval_service=retrieval_service,
    anomaly_service=anomaly_service,
    root_cause_service=root_cause_service,
    llm_service=llm_service,
)

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(router)
