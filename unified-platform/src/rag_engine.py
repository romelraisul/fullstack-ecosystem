import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional
import time

# Use a mock/simulated embedding for MVP if torch/transformers not available
# But I will try to use a simple one if I can.
# For this environment, let's implement a robust similarity interface.

class RAGEngine:
    def __init__(self, index_path: str = "./data/vector_index.bin"):
        self.index_path = index_path
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        logger = logging.getLogger("RAGEngine")
        self.logger = logger

    def add_documents(self, docs: List[Dict[str, Any]]):
        """
        Expects List of {"id": str, "content": str, "metadata": dict}
        """
        self.documents.extend(docs)
        # In real scenario, compute embeddings and build FAISS index
        # For prototype, we'll simulate search
        self.logger.info(f"Added {len(docs)} documents to RAG index.")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        self.logger.info(f"Searching for: {query}")
        start_time = time.time()
        
        # Simulated keyword-based ranking for MVP
        query_words = set(query.lower().split())
        results = []
        for doc in self.documents:
            doc_words = set(doc["content"].lower().split())
            common = query_words.intersection(doc_words)
            score = len(common) / (len(query_words) + 1)
            results.append({"doc": doc, "score": score})
        
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        top_results = results[:top_k]
        
        latency = (time.time() - start_time) * 1000
        self.logger.info(f"Search completed in {latency:.2f}ms")
        
        return top_results

    def sanitize_query(self, query: str) -> str:
        # Basic input sanitization
        return query.strip()[:500] # Limit length

rag_engine = RAGEngine()
