"""Chart-ready JSON for frontend (Chart.js / Recharts)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from . import analyzer as analyzer_mod


def _sanitize(data: Any) -> Any:
    return analyzer_mod._sanitize_for_json(data)


def build_chart_payload(df: pd.DataFrame) -> dict[str, Any]:
    """
    Produce structured chart definitions:
    - line: time series trends
    - bar: categorical distributions
    - heatmap: correlation matrix
    """
    types = analyzer_mod._classify_columns(df)
    numeric = types["numeric"]
    categorical = types["categorical"]
    datetime_cols = types["datetime"]

    charts: dict[str, Any] = {
        "line": [],
        "bar": [],
        "heatmap": None,
    }

    # Used for anomaly overlays on time-series charts.
    numeric_outliers = analyzer_mod._outliers_iqr(df, numeric) if numeric else {}

    # Line charts: datetime x first numeric (or multiple series)
    if datetime_cols and numeric:
        dt_col = datetime_cols[0]
        d = df[[dt_col] + numeric].dropna(subset=[dt_col]).sort_values(dt_col)
        if len(d) > 0:
            labels = [pd.Timestamp(x).isoformat() for x in d[dt_col].tolist()]
            for num in numeric[:5]:
                bounds = numeric_outliers.get(num) or {}
                low = bounds.get("lower_bound")
                high = bounds.get("upper_bound")

                main_data = [None if pd.isna(v) else float(v) for v in d[num].tolist()]
                anomaly_data = None
                if low is not None and high is not None:
                    anomaly_data = []
                    for v in d[num].tolist():
                        if pd.isna(v):
                            anomaly_data.append(None)
                            continue
                        fv = float(v)
                        anomaly_data.append(fv if (fv < low or fv > high) else None)

                datasets: list[dict[str, Any]] = [
                    {
                        "label": str(num),
                        "data": main_data,
                        "fill": True,
                    }
                ]
                if anomaly_data:
                    datasets.append(
                        {
                            "label": f"{num} anomalies (IQR)",
                            "data": anomaly_data,
                            "showLine": False,
                            "fill": False,
                            "borderColor": "rgba(248,113,113,0.95)",
                            "backgroundColor": "rgba(248,113,113,0.9)",
                            "pointRadius": 4,
                            "pointHoverRadius": 6,
                        }
                    )

                charts["line"].append(
                    {
                        "id": f"line_{dt_col}_{num}",
                        "title": f"{num} over time",
                        "labels": labels,
                        "datasets": datasets,
                    }
                )

    # Bar charts: top categories per categorical column
    for cat in categorical[:8]:
        vc = df[cat].astype(str).value_counts().head(15)
        charts["bar"].append(
            {
                "id": f"bar_{cat}",
                "title": f"Distribution of {cat}",
                "labels": [str(k) for k in vc.index.tolist()],
                "datasets": [
                    {
                        "label": "count",
                        "data": [int(v) for v in vc.values.tolist()],
                    }
                ],
            }
        )

    # Heatmap from correlation
    corr_info = analyzer_mod._correlation_matrix(df, numeric)
    cols = corr_info.get("columns", [])
    matrix = corr_info.get("matrix", [])
    if cols and matrix:
        charts["heatmap"] = {
            "id": "corr_heatmap",
            "title": "Correlation heatmap (numeric features)",
            "x_labels": cols,
            "y_labels": cols,
            "values": matrix,
        }

    return _sanitize(charts)


def build_visualize_response(df: pd.DataFrame) -> dict[str, Any]:
    """Public entry used by API."""
    return {"charts": build_chart_payload(df)}
