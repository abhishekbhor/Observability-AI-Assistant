from __future__ import annotations

from collections import Counter

from app.models.schemas import LogEvent, TraceSpan


class RootCauseService:
    def infer(
        self,
        logs: list[LogEvent],
        traces: list[TraceSpan],
        anomalies: list[dict],
    ) -> list[str]:
        hypotheses: list[str] = []

        error_logs = [l for l in logs if l.severity in {"ERROR", "CRITICAL"}]
        if error_logs:
            service_counts = Counter(l.service for l in error_logs)
            service, count = service_counts.most_common(1)[0]
            messages = Counter(l.message for l in error_logs if l.service == service)
            common_msg = messages.most_common(1)[0][0] if messages else "repeated application errors"
            hypotheses.append(
                f"{service} is the strongest application-layer suspect, with {count} high-severity logs; recurring error: '{common_msg}'."
            )

        error_traces = [t for t in traces if t.status == "error"]
        if error_traces:
            slowest = sorted(error_traces, key=lambda x: x.duration_ms, reverse=True)[0]
            if slowest.downstream_service:
                hypotheses.append(
                    f"Trace failures indicate latency or errors flowing from {slowest.service} to downstream dependency {slowest.downstream_service} during operation '{slowest.operation}'."
                )
            else:
                hypotheses.append(
                    f"Trace failures cluster in {slowest.service} around operation '{slowest.operation}', suggesting localized code or dependency issues."
                )

        for anomaly in anomalies[:3]:
            if anomaly["metric_name"].lower() in {"latency_ms", "p95_latency_ms", "error_rate", "cpu_pct"}:
                hypotheses.append(
                    f"Metric anomaly detected in {anomaly['service']} for {anomaly['metric_name']} with z-score {anomaly['z_score']}, indicating abnormal operational behavior."
                )

        if not hypotheses:
            hypotheses.append(
                "No single dominant root cause was found. The incident appears weakly signaled, so expanding the lookback window or adding deployment metadata would help."
            )

        # keep order while de-duplicating
        seen = set()
        unique: list[str] = []
        for item in hypotheses:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        return unique[:5]
