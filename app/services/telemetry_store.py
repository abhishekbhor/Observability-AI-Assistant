from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.models.schemas import LogEvent, MetricPoint, TelemetryBatch, TraceSpan
from app.utils.time import iso_to_dt, utc_now, within_lookback


@dataclass
class TelemetrySnapshot:
    logs: list[LogEvent]
    metrics: list[MetricPoint]
    traces: list[TraceSpan]


class TelemetryStore:
    def __init__(self) -> None:
        self.logs: list[LogEvent] = []
        self.metrics: list[MetricPoint] = []
        self.traces: list[TraceSpan] = []

    def ingest(self, batch: TelemetryBatch) -> dict[str, int]:
        self.logs.extend(batch.logs)
        self.metrics.extend(batch.metrics)
        self.traces.extend(batch.traces)
        self.logs.sort(key=lambda x: x.timestamp)
        self.metrics.sort(key=lambda x: x.timestamp)
        self.traces.sort(key=lambda x: x.timestamp)
        return {
            "logs": len(batch.logs),
            "metrics": len(batch.metrics),
            "traces": len(batch.traces),
        }

    def query(
        self,
        services: list[str] | None = None,
        environment: str = "prod",
        lookback_minutes: int = 120,
    ) -> TelemetrySnapshot:
        services = services or []
        now = utc_now()

        def service_match(service: str) -> bool:
            return not services or service in services

        logs = [
            x
            for x in self.logs
            if x.environment == environment
            and service_match(x.service)
            and within_lookback(x.timestamp, lookback_minutes, now=now)
        ]
        metrics = [
            x
            for x in self.metrics
            if x.environment == environment
            and service_match(x.service)
            and within_lookback(x.timestamp, lookback_minutes, now=now)
        ]
        traces = [
            x
            for x in self.traces
            if x.environment == environment
            and service_match(x.service)
            and within_lookback(x.timestamp, lookback_minutes, now=now)
        ]
        return TelemetrySnapshot(logs=logs, metrics=metrics, traces=traces)

    def service_map(self, traces: list[TraceSpan]) -> dict[str, list[str]]:
        graph: dict[str, set[str]] = defaultdict(set)
        for span in traces:
            if span.downstream_service:
                graph[span.service].add(span.downstream_service)
                graph.setdefault(span.downstream_service, set())
            else:
                graph.setdefault(span.service, set())
        return {svc: sorted(list(children)) for svc, children in sorted(graph.items())}

    def clear(self) -> None:
        self.logs.clear()
        self.metrics.clear()
        self.traces.clear()
