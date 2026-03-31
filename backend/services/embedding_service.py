"""Embedding service using SentenceTransformers with robust fallback."""

from __future__ import annotations

import hashlib
import os
from typing import Any

import numpy as np
from openai import OpenAI


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dim_fallback: int = 384):
        self.model_name = model_name
        self.dim_fallback = dim_fallback
        self._st_model = None
        self._openai = None

    def _init_st(self) -> None:
        if self._st_model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._st_model = SentenceTransformer(self.model_name)
        except Exception:
            self._st_model = None

    def _init_openai(self) -> None:
        if self._openai is not None:
            return
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if key:
            self._openai = OpenAI(api_key=key)

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    def _hash_embed(self, texts: list[str]) -> np.ndarray:
        vecs = np.zeros((len(texts), self.dim_fallback), dtype=np.float32)
        for i, t in enumerate(texts):
            for tok in t.lower().split():
                idx = int.from_bytes(hashlib.sha256(tok.encode("utf-8")).digest()[:8], "little") % self.dim_fallback
                vecs[i, idx] += 1.0
        return self._normalize(vecs)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim_fallback), dtype=np.float32)

        self._init_st()
        if self._st_model is not None:
            arr = self._st_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return arr.astype(np.float32)

        self._init_openai()
        if self._openai is not None:
            try:
                res = self._openai.embeddings.create(model="text-embedding-3-small", input=texts)
                arr = np.array([d.embedding for d in res.data], dtype=np.float32)
                return self._normalize(arr)
            except Exception:
                pass

        return self._hash_embed(texts)


embedding_service = EmbeddingService()

