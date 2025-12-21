import time
import logging
from typing import Dict, Any

logger = logging.getLogger("Monitoring")

class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "errors_total": 0,
            "latency_ms": [],
            "rag_relevance_scores": []
        }

    def record_request(self, latency: float, success: bool = True):
        self.metrics["requests_total"] += 1
        if not success:
            self.metrics["errors_total"] += 1
        self.metrics["latency_ms"].append(latency * 1000)
        # Keep only last 1000 for memory
        if len(self.metrics["latency_ms"]) > 1000:
            self.metrics["latency_ms"].pop(0)

    def record_rag_score(self, score: float):
        self.metrics["rag_relevance_scores"].append(score)
        if len(self.metrics["rag_relevance_scores"]) > 1000:
            self.metrics["rag_relevance_scores"].pop(0)

    def get_kpis(self) -> Dict[str, Any]:
        avg_latency = sum(self.metrics["latency_ms"]) / max(len(self.metrics["latency_ms"]), 1)
        avg_relevance = sum(self.metrics["rag_relevance_scores"]) / max(len(self.metrics["rag_relevance_scores"]), 1)
        error_rate = (self.metrics["errors_total"] / max(self.metrics["requests_total"], 1)) * 100
        
        return {
            "avg_latency_ms": round(avg_latency, 2),
            "avg_rag_relevance": round(avg_relevance, 2),
            "error_rate_pct": round(error_rate, 2),
            "total_requests": self.metrics["requests_total"]
        }

monitor = MetricsCollector()
