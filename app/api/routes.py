from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.models.schemas import HealthResponse, InvestigationRequest, InvestigationResponse, TelemetryBatch
from app.services.assistant import ObservabilityAssistant
from app.services.telemetry_store import TelemetryStore

router = APIRouter()


def get_store() -> TelemetryStore:
    from app.main import store

    return store


def get_assistant() -> ObservabilityAssistant:
    from app.main import assistant

    return assistant


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", app_name=settings.app_name, version=settings.app_version)


@router.post("/telemetry/batch")
def ingest_telemetry(batch: TelemetryBatch, store: TelemetryStore = Depends(get_store)) -> dict:
    counts = store.ingest(batch)
    return {"status": "ingested", "counts": counts}


@router.post("/telemetry/reset")
def reset_telemetry(store: TelemetryStore = Depends(get_store)) -> dict:
    store.clear()
    return {"status": "cleared"}


@router.post("/assistant/investigate", response_model=InvestigationResponse)
def investigate(
    request: InvestigationRequest,
    obs_assistant: ObservabilityAssistant = Depends(get_assistant),
) -> InvestigationResponse:
    return obs_assistant.investigate(request)
