"""Chat-with-data: OpenAI when configured, otherwise rule-based answers from EDA."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI

from . import analyzer as analyzer_mod


def _compact_context(eda: dict[str, Any]) -> dict[str, Any]:
    return {
        "column_types": eda.get("column_types"),
        "summary_statistics": eda.get("summary_statistics"),
        "correlation": eda.get("correlation"),
        "trends": eda.get("trends"),
        "outliers": eda.get("outliers"),
        "missing_values": eda.get("missing_values"),
        "categorical_frequency": eda.get("categorical_frequency"),
    }


def _rule_based_answer(eda: dict[str, Any], question: str) -> dict[str, Any]:
    q = (question or "").strip().lower()
    col_types = eda.get("column_types") or {}
    numeric = col_types.get("numeric") or []
    categorical = col_types.get("categorical") or []
    dt_cols = col_types.get("datetime") or []
    missing = eda.get("missing_values") or {}
    total_rows = missing.get("total_rows")
    corr = eda.get("correlation") or {}
    cols = corr.get("columns") or []
    mat = corr.get("matrix") or []
    outliers = eda.get("outliers") or {}
    trends = eda.get("trends") or {}
    summary = eda.get("summary_statistics") or {}
    cat_freq = eda.get("categorical_frequency") or {}

    parts: list[str] = []
    confidence = "low"

    def add_correlations(top_n: int = 5) -> None:
        nonlocal confidence
        pairs: list[tuple[str, str, float]] = []
        if cols and mat and len(cols) >= 2:
            for i, a in enumerate(cols):
                for j, b in enumerate(cols):
                    if j <= i:
                        continue
                    val = mat[i][j]
                    if val is not None:
                        pairs.append((a, b, float(val)))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        if not pairs:
            parts.append("There are not enough numeric columns to compute pairwise correlations.")
            return
        confidence = "medium"
        lines = [f"- {a} vs {b}: {v:+.3f}" for a, b, v in pairs[:top_n]]
        parts.append("Strongest linear correlations (Pearson) among numeric columns:\n" + "\n".join(lines))

    if any(k in q for k in ("correlation", "correlate", "correlated")):
        add_correlations()

    if any(k in q for k in ("outlier", "outliers", "anomaly", "anomalies")):
        confidence = "medium"
        items = [(c, o.get("outlier_count", 0)) for c, o in outliers.items() if o.get("outlier_count", 0) > 0]
        items.sort(key=lambda x: x[1], reverse=True)
        if not items:
            parts.append("No IQR-based outliers were flagged for numeric columns (or there are no numeric columns).")
        else:
            top = ", ".join(f"{c} ({n})" for c, n in items[:6])
            parts.append(f"Columns with the most flagged outliers (IQR rule): {top}.")

    if any(k in q for k in ("missing", "null", "na ", "n/a", "incomplete")):
        confidence = "medium"
        by_col = missing.get("by_column") or []
        bad = [r for r in by_col if (r.get("missing_pct") or 0) > 0]
        if not bad:
            parts.append("After cleaning, no missing values remain in the profiled columns.")
        else:
            worst = sorted(bad, key=lambda r: r.get("missing_pct") or 0, reverse=True)[:6]
            bits = [f"{r.get('column')}: {r.get('missing_pct')}% missing" for r in worst]
            parts.append("Missing-value profile (after cleaning): " + "; ".join(bits) + ".")

    if any(k in q for k in ("trend", "time", "over time", "datetime", "season")):
        confidence = "medium"
        by_metric = trends.get("by_metric") if isinstance(trends, dict) else {}
        if not dt_cols:
            parts.append("No datetime column was detected, so time-series trends are limited.")
        elif not by_metric:
            parts.append("Datetime was detected but trend metrics could not be computed (insufficient points).")
        else:
            bits = []
            for m, t in list(by_metric.items())[:8]:
                direction = t.get("direction")
                pct = t.get("approx_pct_change")
                bits.append(
                    f"{m}: trend looks {direction}"
                    + (f" (~{pct:.1f}% end-to-end)" if pct is not None else "")
                )
            parts.append("Trend hints: " + "; ".join(bits) + ".")

    if any(k in q for k in ("categor", "frequency", "distribution", "top value", "mode")):
        confidence = "medium"
        if not cat_freq:
            parts.append("No categorical columns were identified for frequency analysis.")
        else:
            lines = []
            for col, data in list(cat_freq.items())[:5]:
                tops = data.get("top_values") or []
                if tops:
                    top = tops[0]
                    lines.append(f"{col}: most common is '{top.get('value')}' ({top.get('count')} rows)")
            if lines:
                parts.append("Categorical highlights: " + " | ".join(lines) + ".")

    # Column-specific numeric stats: "what is the mean of X"
    for col in numeric:
        if col.lower() in q and any(k in q for k in ("mean", "average", "median", "std", "min", "max")):
            confidence = "medium"
            s = summary.get(col) or {}
            if s:
                parts.append(
                    f"For '{col}': mean={s.get('mean')}, median={s.get('median')}, "
                    f"std={s.get('std')}, min={s.get('min')}, max={s.get('max')}."
                )

    if not parts:
        overview = []
        if total_rows is not None:
            overview.append(f"The dataset has {total_rows} row(s) after cleaning.")
        overview.append(
            f"Columns: {len(numeric)} numeric, {len(categorical)} categorical, {len(dt_cols)} datetime."
        )
        parts.append(" ".join(overview))
        parts.append(
            "Try asking about correlations, outliers, missing values, trends (if a date column exists), or categorical frequencies."
        )

    answer = "\n\n".join(parts)
    return {"answer": answer.strip(), "confidence": confidence}


def _openai_chat(
    context: dict[str, Any],
    question: str,
    *,
    retrieved_context: list[str] | None = None,
) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        payload = json.dumps(context, default=str)[:16000]
        retrieved_text = ""
        if retrieved_context:
            retrieved_text = "\n\n".join(retrieved_context[:8])[:8000]
        user_msg = (
            "You are given structured exploratory data analysis (EDA) for ONE dataset. "
            "Answer the user's question using ONLY this information. "
            "If the EDA does not contain enough information, say what is missing and what can still be inferred.\n\n"
            f"EDA_CONTEXT_JSON:\n{payload}\n\n"
            + (f"RETRIEVED_SEMANTIC_CONTEXT:\n{retrieved_text}\n\n" if retrieved_text else "")
            + f"USER_QUESTION:\n{question.strip()}"
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior data analyst. Be concise, accurate, and business-friendly. "
                        "Do not invent numbers that are not supported by the EDA context."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=900,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return None
        conf = "high" if len(text) > 180 else "medium"
        return {"answer": text, "confidence": conf}
    except Exception:
        return None


def _normalize_confidence(value: Any) -> str:
    v = str(value or "").lower().strip()
    if v in ("high", "medium", "low"):
        return v
    return "medium"


def chat_with_data(
    eda: dict[str, Any],
    question: str,
    *,
    retrieved_context: list[str] | None = None,
) -> dict[str, Any]:
    """
    Return {"answer": str, "confidence": "high"|"medium"|"low"}.
    """
    q = (question or "").strip()
    if not q:
        return {"answer": "Please provide a non-empty question.", "confidence": "low"}

    ctx = _compact_context(eda)
    llm = _openai_chat(ctx, q, retrieved_context=retrieved_context)
    if llm:
        out = analyzer_mod._sanitize_for_json(llm)
        return {
            "answer": str(out.get("answer", "")),
            "confidence": _normalize_confidence(out.get("confidence", "high")),
        }

    rb = _rule_based_answer(eda, q)
    out = analyzer_mod._sanitize_for_json(rb)
    return {
        "answer": str(out.get("answer", "")),
        "confidence": _normalize_confidence(out.get("confidence", "medium")),
    }


def chat_stream_with_data(
    eda: dict[str, Any],
    question: str,
    *,
    retrieved_context: list[str] | None = None,
):
    """
    Stream NDJSON for real-time chat UX.

    Yields:
      {"type":"token","token":"..."} (repeated)
      {"type":"final","answer":"...","confidence":"high|medium|low"} (once)
    """
    q = (question or "").strip()
    if not q:
        yield json.dumps({"type": "final", "answer": "Please provide a non-empty question.", "confidence": "low"}) + "\n"
        return

    ctx = _compact_context(eda)
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    retrieved_text = "\n\n".join((retrieved_context or [])[:8])[:8000] if retrieved_context else ""

    if not api_key:
        rb = _rule_based_answer(eda, q)
        out = analyzer_mod._sanitize_for_json(rb)
        answer = str(out.get("answer", "")).strip()
        confidence = _normalize_confidence(out.get("confidence", "medium"))

        # Chunk by ~20 words for smoother typing.
        words = answer.split()
        buf: list[str] = []
        for w in words:
            buf.append(w)
            if len(buf) >= 20:
                yield json.dumps({"type": "token", "token": " ".join(buf) + " "}) + "\n"
                buf = []
        if buf:
            yield json.dumps({"type": "token", "token": " ".join(buf)}) + "\n"
        yield json.dumps({"type": "final", "answer": answer, "confidence": confidence}) + "\n"
        return

    full = ""
    try:
        client = OpenAI(api_key=api_key)
        payload = json.dumps(ctx, default=str)[:16000]
        user_msg = (
            "You are given structured exploratory data analysis (EDA) for ONE dataset. "
            "Answer the user's question using ONLY this information.\n\n"
            f"EDA_CONTEXT_JSON:\n{payload}\n\n"
            + (f"RETRIEVED_SEMANTIC_CONTEXT:\n{retrieved_text}\n\n" if retrieved_text else "")
            + f"USER_QUESTION:\n{q}"
        )
        stream = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior data analyst. Be concise, accurate, and business-friendly. "
                        "Do not invent numbers not present in the EDA context."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=900,
            stream=True,
        )

        for event in stream:
            delta = event.choices[0].delta
            token = getattr(delta, "content", None)
            if token:
                full += token
                yield json.dumps({"type": "token", "token": token}) + "\n"

        confidence = "high" if retrieved_context else "medium"
        yield json.dumps({"type": "final", "answer": full.strip(), "confidence": confidence}) + "\n"
    except Exception:
        rb = _rule_based_answer(eda, q)
        out = analyzer_mod._sanitize_for_json(rb)
        answer = str(out.get("answer", "")).strip()
        confidence = _normalize_confidence(out.get("confidence", "medium"))
        yield json.dumps({"type": "token", "token": answer}) + "\n"
        yield json.dumps({"type": "final", "answer": answer, "confidence": confidence}) + "\n"
