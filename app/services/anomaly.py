from __future__ import annotations

from collections import defaultdict

import numpy as np

from app.models.schemas import MetricPoint


class AnomalyService:
    def detect(self, metrics: list[MetricPoint], z_threshold: float = 2.0) -> list[dict]:
        grouped: dict[tuple[str, str], list[MetricPoint]] = defaultdict(list)
        for point in metrics:
            grouped[(point.service, point.metric_name)].append(point)

        anomalies: list[dict] = []
        for (service, metric_name), points in grouped.items():
            points = sorted(points, key=lambda p: p.timestamp)
            values = np.array([p.value for p in points], dtype=float)
            if len(values) < 3:
                continue
            mean = float(values.mean())
            std = float(values.std())
            if std == 0:
                continue
            latest = points[-1]
            z = (latest.value - mean) / std
            if abs(z) >= z_threshold:
                anomalies.append(
                    {
                        "service": service,
                        "metric_name": metric_name,
                        "timestamp": latest.timestamp.isoformat(),
                        "value": latest.value,
                        "baseline_mean": round(mean, 3),
                        "baseline_std": round(std, 3),
                        "z_score": round(float(z), 3),
                        "direction": "up" if z > 0 else "down",
                    }
                )
        anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)
        return anomalies
