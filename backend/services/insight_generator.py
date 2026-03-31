"""LLM-powered insights with deterministic fallback."""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from . import analyzer as analyzer_mod


def _fallback_insights(eda: dict[str, Any]) -> dict[str, Any]:
    """Rule-based insights when no API key or on model failure."""
    col_types = eda.get("column_types", {})
    numeric = col_types.get("numeric", [])
    categorical = col_types.get("categorical", [])
    dt_cols = col_types.get("datetime", [])

    summary = eda.get("summary_statistics", {})
    corr = eda.get("correlation", {})
    outliers = eda.get("outliers", {})
    trends = eda.get("trends", {})
    missing = eda.get("missing_values", {})

    exec_lines = [
        "This dataset was profiled automatically using descriptive statistics, correlations, and frequency analysis.",
    ]
    if numeric:
        exec_lines.append(f"The analysis covers {len(numeric)} numeric column(s), enabling correlation and outlier review.")
    if dt_cols:
        exec_lines.append("A datetime column was detected, so time-based trends were estimated.")
    else:
        exec_lines.append("No datetime column was detected; trend analysis is limited to cross-sectional patterns.")

    findings: list[str] = []
    strong_pairs: list[tuple[str, str, float]] = []

    # Strong correlations
    cols = corr.get("columns", [])
    mat = corr.get("matrix", [])
    if cols and len(cols) >= 2 and mat:
        for i, a in enumerate(cols):
            for j, b in enumerate(cols):
                if j <= i:
                    continue
                val = mat[i][j]
                if val is not None and abs(val) >= 0.7:
                    strong_pairs.append((a, b, float(val)))
        strong_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        for a, b, v in strong_pairs[:5]:
            findings.append(f"Strong correlation ({v:+.2f}) between '{a}' and '{b}'.")

    # Outliers
    for col, info in list(outliers.items())[:5]:
        cnt = info.get("outlier_count", 0)
        if cnt > 0:
            findings.append(f"Column '{col}' shows {cnt} potential outlier(s) via the IQR rule.")

    # Trends
    by_metric = trends.get("by_metric", {}) if isinstance(trends, dict) else {}
    for m, t in list(by_metric.items())[:5]:
        direction = t.get("direction")
        pct = t.get("approx_pct_change")
        if direction and direction != "flat":
            findings.append(
                f"Time trend for '{m}' appears {direction}"
                + (f" (approx. {pct:.1f}% change end-to-end)." if pct is not None else ".")
            )

    # Missing data
    for row in missing.get("by_column", [])[:8]:
        mp = row.get("missing_pct", 0) or 0
        if mp > 5:
            findings.append(f"Column '{row.get('column')}' has {mp:.1f}% missing values after cleaning.")

    # Categorical concentration
    cat_freq = eda.get("categorical_frequency", {})
    for col, data in list(cat_freq.items())[:5]:
        tops = data.get("top_values", [])
        if len(tops) >= 1:
            top = tops[0]
            findings.append(
                f"Most frequent category in '{col}' is '{top.get('value')}' ({top.get('count')} rows)."
            )

    anomalies: list[dict[str, Any]] = []
    if isinstance(outliers, dict) and outliers:
        for col, info in outliers.items():
            cnt = int(info.get("outlier_count") or 0)
            if cnt > 0:
                anomalies.append({"column": col, "outlier_count": cnt})
        anomalies.sort(key=lambda x: x["outlier_count"], reverse=True)
        anomalies = anomalies[:10]

    recommendations: list[str] = [
        "Validate outliers with domain knowledge before excluding them from modeling.",
        "Consider feature scaling for numeric columns if you plan to use distance-based models.",
        "Document assumptions for missing-value treatment; business context may prefer different imputation.",
    ]
    if strong_pairs:
        recommendations.append("Explore multicollinearity before regression; highly correlated features may be redundant.")
    if categorical:
        recommendations.append("Review high-cardinality categorical columns for grouping or encoding strategy.")

    return {
        "executive_summary": " ".join(exec_lines),
        "key_findings": findings[:12] if findings else ["No strong automated patterns flagged; dataset appears relatively regular."],
        "business_recommendations": recommendations[:8],
        "anomalies": anomalies,
        "model": "rule_based_fallback",
    }


def generate_insights(eda: dict[str, Any]) -> dict[str, Any]:
    """Return structured insights; uses OpenAI when OPENAI_API_KEY is set."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        result = _fallback_insights(eda)
        return analyzer_mod._sanitize_for_json(result)

    try:
        client = OpenAI(api_key=api_key)
        prompt = _build_prompt(eda)
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior data strategist. Given structured EDA output, respond ONLY with valid JSON "
                        "matching this schema: "
                        '{"executive_summary": string, "key_findings": string[], "business_recommendations": string[], "anomalies": array}. '
                        "Be concise, actionable, and business-oriented. No markdown, no code fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1200,
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = _parse_json_object(text)
        if parsed:
            parsed["model"] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            return analyzer_mod._sanitize_for_json(parsed)
    except Exception:
        pass

    result = _fallback_insights(eda)
    return analyzer_mod._sanitize_for_json(result)


def _build_prompt(eda: dict[str, Any]) -> str:
    import json

    payload = {
        "summary_statistics": eda.get("summary_statistics"),
        "correlation": eda.get("correlation"),
        "missing_values": eda.get("missing_values"),
        "outliers": eda.get("outliers"),
        "trends": eda.get("trends"),
        "categorical_frequency": eda.get("categorical_frequency"),
        "column_types": eda.get("column_types"),
    }
    return (
        "Analyze the following EDA JSON. Highlight correlations, trends, anomalies/outliers, data quality risks, "
        "and practical business implications.\n\n"
        + json.dumps(payload, default=str)[:24000]
    )


def _parse_json_object(text: str) -> dict[str, Any] | None:
    import json
    import re

    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "executive_summary" in obj:
            return obj
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            obj = json.loads(m.group())
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            return None
    return None
