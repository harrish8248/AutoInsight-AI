"""Vector store with real embeddings + cosine retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np

from .embedding_service import embedding_service


_TOKEN_RE = re.compile(r"[\w']+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _cosine_sim_matrix(q_vec: np.ndarray, mat: np.ndarray) -> np.ndarray:
    # embeddings are normalized; cosine = dot
    return mat @ q_vec


def _docs_from_eda(eda: dict[str, Any]) -> list[str]:
    """
    Convert EDA JSON into semantically searchable text documents.
    Keep it compact for speed and to limit prompt size.
    """
    docs: list[str] = []
    col_types = eda.get("column_types") or {}
    numeric = col_types.get("numeric") or []
    categorical = col_types.get("categorical") or []
    datetime_cols = col_types.get("datetime") or []

    summary = eda.get("summary_statistics") or {}
    missing = eda.get("missing_values") or {}
    corr = eda.get("correlation") or {}
    outliers = eda.get("outliers") or {}
    trends = eda.get("trends") or {}
    cat_freq = eda.get("categorical_frequency") or {}

    rows = missing.get("total_rows")
    docs.append(
        "DATASET OVERVIEW: "
        f"rows={rows}, numeric_columns={len(numeric)}, categorical_columns={len(categorical)}, "
        f"datetime_columns={len(datetime_cols)}"
    )

    # Summary stats for up to 8 numeric columns
    for col in numeric[:8]:
        s = summary.get(col) or {}
        docs.append(
            f"NUMERIC SUMMARY {col}: mean={s.get('mean')}, median={s.get('median')}, std={s.get('std')}, "
            f"min={s.get('min')}, max={s.get('max')}"
        )

    # Missing values profile (top 6 by missing_pct)
    by_col = missing.get("by_column") or []
    if isinstance(by_col, list) and by_col:
        sorted_missing = sorted(by_col, key=lambda r: float(r.get("missing_pct") or 0), reverse=True)[:6]
        bits = ", ".join([f"{r.get('column')}: {r.get('missing_pct')}% missing" for r in sorted_missing])
        docs.append(f"MISSING VALUES: {bits}")

    # Correlation top pairs
    cols = corr.get("columns") or []
    matrix = corr.get("matrix") or []
    if cols and matrix and len(cols) >= 2:
        pairs: list[str] = []
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = matrix[i][j] if i < len(matrix) and j < len(matrix[i]) else None
                if val is None:
                    continue
                if abs(val) >= 0.5:
                    pairs.append(f"{cols[i]} vs {cols[j]}: {val:+.3f}")
        if pairs:
            # keep top by abs correlation
            pairs_sorted = sorted(pairs, key=lambda s: abs(float(s.split(":")[1])), reverse=True)[:8]
            docs.append("CORRELATIONS (|r|>=0.5): " + "; ".join(pairs_sorted))

    # Trends: up to 6 metrics
    if isinstance(trends, dict) and trends:
        by_metric = trends.get("by_metric") if "by_metric" in trends else trends
        if isinstance(by_metric, dict):
            items = list(by_metric.items())[:6]
            bits = "; ".join(
                [
                    f"{m}: {t.get('direction')} (slope={t.get('slope_estimate')})"
                    for m, t in items
                    if isinstance(t, dict)
                ]
            )
            docs.append("TRENDS: " + bits)

    # Outliers: top 6
    if isinstance(outliers, dict) and outliers:
        items = sorted(
            outliers.items(), key=lambda kv: int(kv[1].get("outlier_count") or 0), reverse=True
        )[:6]
        bits = "; ".join([f"{col}: outlier_count={info.get('outlier_count')}" for col, info in items])
        if bits:
            docs.append("OUTLIERS (IQR): " + bits)

    # Categorical frequency highlights
    if isinstance(cat_freq, dict) and cat_freq:
        for col, data in list(cat_freq.items())[:4]:
            tops = data.get("top_values") or []
            if tops:
                top = tops[0]
                docs.append(f"CATEGORY HIGHLIGHT {col}: top='{top.get('value')}', count={top.get('count')}")

    return docs[:40]


@dataclass
class VectorIndex:
    dim: int
    docs: list[str]
    doc_vectors: np.ndarray


class VectorStoreManager:
    """
    Session-local in-memory semantic index.
    """

    def __init__(self):
        self._indexes: dict[str, VectorIndex] = {}

    def ensure_built(self, session_id: str, eda: dict[str, Any]) -> None:
        if session_id in self._indexes:
            return
        docs = _docs_from_eda(eda)
        doc_vecs = embedding_service.embed_texts(docs)
        dim = int(doc_vecs.shape[1]) if len(doc_vecs.shape) == 2 and doc_vecs.shape[0] else 384
        self._indexes[session_id] = VectorIndex(dim=dim, docs=docs, doc_vectors=doc_vecs)

    def query(self, session_id: str, question: str, *, top_k: int = 5) -> list[dict[str, Any]]:
        idx = self._indexes.get(session_id)
        if not idx:
            return []
        q_vec = embedding_service.embed_texts([question])[0]
        if float(np.linalg.norm(q_vec)) == 0.0:
            return []
        q_vec_norm = q_vec / (float(np.linalg.norm(q_vec)) or 1.0)
        sims = _cosine_sim_matrix(q_vec_norm, idx.doc_vectors)
        order = np.argsort(-sims)[:top_k]
        out: list[dict[str, Any]] = []
        for i in order.tolist():
            out.append({"doc": idx.docs[i], "score": float(sims[i])})
        return out


# Singleton used by API layer
vector_store = VectorStoreManager()

