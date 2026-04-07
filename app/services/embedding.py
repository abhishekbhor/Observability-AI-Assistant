from __future__ import annotations

import hashlib
import math
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from app.core.config import settings


@dataclass
class EmbeddingRuntime:
    mode: str
    gpu_available: bool
    gpu_workers: int


class EmbeddingService:
    """
    Lightweight deterministic embedding service.

    Why deterministic embeddings here?
    - keeps the project runnable without downloading large models
    - still supports retrieval and similarity search
    - gives you a clean seam for swapping in a real embedding model later

    Multi-GPU note:
    In a production setup this class is where you would shard text batches across
    GPUs using torch / vLLM / Ray / Dask. This implementation keeps the API shape
    and execution model, while remaining dependency-light.
    """

    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or settings.embedding_dim
        self.runtime = EmbeddingRuntime(
            mode="deterministic-hash",
            gpu_available=self._cuda_available(),
            gpu_workers=max(1, settings.gpu_workers),
        )

    def _cuda_available(self) -> bool:
        if not settings.enable_gpu:
            return False
        try:
            import torch  # type: ignore

            return bool(torch.cuda.is_available())
        except Exception:
            return False

    def embed_text(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = text.lower().split()
        if not tokens:
            return vec
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i in range(self.dim):
                vec[i] += digest[i % len(digest)] / 255.0
        norm = np.linalg.norm(vec)
        return vec if norm == 0 else vec / norm

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)

        if self.runtime.gpu_available and self.runtime.gpu_workers > 1 and len(texts) >= 32:
            return self._distributed_embed(texts)

        return np.vstack([self.embed_text(t) for t in texts])

    def _distributed_embed(self, texts: list[str]) -> np.ndarray:
        chunks = self._chunk(texts, self.runtime.gpu_workers)
        with ProcessPoolExecutor(max_workers=self.runtime.gpu_workers) as ex:
            arrays = list(ex.map(_embed_chunk_worker, [(chunk, self.dim) for chunk in chunks]))
        return np.vstack(arrays)

    @staticmethod
    def cosine_similarity(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
        if len(doc_matrix) == 0:
            return np.array([], dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return np.zeros(len(doc_matrix), dtype=np.float32)
        doc_norms = np.linalg.norm(doc_matrix, axis=1)
        denom = np.clip(doc_norms * query_norm, 1e-8, None)
        return (doc_matrix @ query_vec) / denom

    @staticmethod
    def _chunk(items: list[str], n: int) -> list[list[str]]:
        size = max(1, math.ceil(len(items) / n))
        return [items[i : i + size] for i in range(0, len(items), size)]


def _embed_chunk_worker(args: tuple[list[str], int]) -> np.ndarray:
    texts, dim = args
    service = EmbeddingService(dim=dim)
    return np.vstack([service.embed_text(t) for t in texts]) if texts else np.zeros((0, dim), dtype=np.float32)
