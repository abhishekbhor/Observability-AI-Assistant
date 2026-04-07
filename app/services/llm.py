from __future__ import annotations

from app.core.config import settings


class LLMService:
    def summarize(
        self,
        question: str,
        likely_root_causes: list[str],
        anomalies: list[dict],
        evidence: list[dict],
    ) -> str:
        if settings.llm_mode == "heuristic":
            parts: list[str] = [f"Investigation question: {question}"]
            if likely_root_causes:
                parts.append("Top likely causes: " + " ".join(likely_root_causes[:3]))
            if anomalies:
                parts.append(
                    "Key anomalies: "
                    + "; ".join(
                        f"{a['service']} {a['metric_name']}={a['value']} (z={a['z_score']})" for a in anomalies[:3]
                    )
                )
            if evidence:
                parts.append(
                    "Most relevant evidence came from "
                    + ", ".join(f"{e['source_type']}:{e['service']}" for e in evidence[:5])
                    + "."
                )
            return " ".join(parts)

        return (
            "External LLM mode is not configured in this starter project. "
            "Replace app/services/llm.py with your provider integration."
        )
