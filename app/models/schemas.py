from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]


class LogEvent(BaseModel):
    timestamp: datetime
    service: str
    environment: str = "prod"
    severity: Severity = "INFO"
    message: str
    host: str | None = None
    trace_id: str | None = None
    incident_id: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class MetricPoint(BaseModel):
    timestamp: datetime
    service: str
    environment: str = "prod"
    metric_name: str
    value: float
    unit: str | None = None
    host: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class TraceSpan(BaseModel):
    timestamp: datetime
    service: str
    environment: str = "prod"
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    operation: str
    duration_ms: float
    status: Literal["ok", "error"] = "ok"
    error_message: str | None = None
    downstream_service: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class TelemetryBatch(BaseModel):
    logs: list[LogEvent] = Field(default_factory=list)
    metrics: list[MetricPoint] = Field(default_factory=list)
    traces: list[TraceSpan] = Field(default_factory=list)


class InvestigationRequest(BaseModel):
    question: str
    services: list[str] = Field(default_factory=list)
    environment: str = "prod"
    lookback_minutes: int = 120
    top_k: int = 8


class InvestigationResponse(BaseModel):
    question: str
    summary: str
    likely_root_causes: list[str]
    anomalies: list[dict]
    evidence: list[dict]
    service_map: dict[str, list[str]]


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
