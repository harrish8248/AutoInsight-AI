"""Exploratory data analysis utilities."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _to_python(obj: Any) -> Any:
    """Convert numpy/pandas scalars to JSON-serializable Python types."""
    if obj is None or isinstance(obj, (bool, str)):
        return obj
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        if np.isnan(obj):
            return None
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            pass
    return obj


def _sanitize_for_json(data: Any) -> Any:
    if isinstance(data, dict):
        return {str(k): _sanitize_for_json(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_sanitize_for_json(x) for x in data]
    if isinstance(data, (pd.Series,)):
        return _sanitize_for_json(data.to_dict())
    if isinstance(data, (pd.DataFrame,)):
        return _sanitize_for_json(data.to_dict(orient="split"))
    return _to_python(data)


def _classify_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    numeric: list[str] = []
    categorical: list[str] = []
    datetime_cols: list[str] = []

    for col in df.columns:
        s = df[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            datetime_cols.append(col)
        elif pd.api.types.is_numeric_dtype(s):
            numeric.append(col)
        else:
            # Treat as categorical (including object strings)
            categorical.append(col)

    return {
        "numeric": numeric,
        "categorical": categorical,
        "datetime": datetime_cols,
    }


def _missing_report(df: pd.DataFrame) -> dict[str, Any]:
    total = len(df)
    rows: list[dict[str, Any]] = []
    for col in df.columns:
        missing = int(df[col].isna().sum())
        rows.append(
            {
                "column": col,
                "missing_count": missing,
                "missing_pct": round(100.0 * missing / total, 4) if total else 0.0,
            }
        )
    return {"total_rows": total, "by_column": rows}


def _summary_statistics(df: pd.DataFrame, numeric_cols: list[str]) -> dict[str, Any]:
    if not numeric_cols:
        return {}
    desc = df[numeric_cols].describe().T
    out: dict[str, Any] = {}
    for col in numeric_cols:
        row = desc.loc[col] if col in desc.index else None
        if row is None:
            continue
        out[col] = {
            "count": _to_python(row.get("count")),
            "mean": _to_python(row.get("mean")),
            "std": _to_python(row.get("std")),
            "min": _to_python(row.get("min")),
            "25%": _to_python(row.get("25%")),
            "50%": _to_python(row.get("50%")),
            "75%": _to_python(row.get("75%")),
            "max": _to_python(row.get("max")),
        }
        series = df[col].dropna()
        if len(series):
            out[col]["median"] = _to_python(float(series.median()))
    return out


def _correlation_matrix(df: pd.DataFrame, numeric_cols: list[str]) -> dict[str, Any]:
    if len(numeric_cols) < 2:
        return {"columns": numeric_cols, "matrix": []}
    corr = df[numeric_cols].corr(numeric_only=True)
    cols = [str(c) for c in corr.columns]
    matrix = []
    for i, ri in enumerate(cols):
        row = []
        for j, _ in enumerate(cols):
            val = corr.iloc[i, j]
            row.append(None if pd.isna(val) else float(val))
        matrix.append(row)
    return {"columns": cols, "matrix": matrix}


def _outliers_iqr(df: pd.DataFrame, numeric_cols: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) < 4:
            result[col] = {"lower_bound": None, "upper_bound": None, "outlier_count": 0, "outlier_indices_sample": []}
            continue
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        iqr = q3 - q1
        low = q1 - 1.5 * iqr
        high = q3 + 1.5 * iqr
        mask = (df[col] < low) | (df[col] > high)
        idx = df.index[mask].tolist()[:50]
        result[col] = {
            "lower_bound": low,
            "upper_bound": high,
            "outlier_count": int(mask.sum()),
            "outlier_indices_sample": [int(i) for i in idx],
        }
    return result


def _trend_for_datetime(df: pd.DataFrame, dt_col: str, numeric_cols: list[str]) -> dict[str, Any]:
    trends: dict[str, Any] = {}
    d = df[[dt_col] + [c for c in numeric_cols if c in df.columns]].dropna(subset=[dt_col])
    if len(d) < 3:
        return {"datetime_column": dt_col, "series": []}

    d = d.sort_values(dt_col)
    for num in numeric_cols:
        if num not in d.columns:
            continue
        sub = d[[dt_col, num]].dropna()
        if len(sub) < 3:
            continue
        y = sub[num].astype(float).values
        x = np.arange(len(y), dtype=float)
        slope = float(np.polyfit(x, y, 1)[0]) if len(y) >= 2 else 0.0
        first, last = float(y[0]), float(y[-1])
        pct = ((last - first) / abs(first) * 100.0) if first != 0 else None
        trends[num] = {
            "direction": "up" if slope > 0 else ("down" if slope < 0 else "flat"),
            "slope_estimate": slope,
            "first_value": first,
            "last_value": last,
            "approx_pct_change": round(pct, 4) if pct is not None else None,
            "points_used": len(y),
        }
    return {"datetime_column": dt_col, "by_metric": trends}


def _categorical_frequency(df: pd.DataFrame, categorical_cols: list[str], top_n: int = 20) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in categorical_cols:
        vc = df[col].astype(str).value_counts().head(top_n)
        out[col] = {
            "unique_count": int(df[col].nunique(dropna=True)),
            "top_values": [{"value": str(k), "count": int(v)} for k, v in vc.items()],
        }
    return out


def analyze(df: pd.DataFrame) -> dict[str, Any]:
    """Run full EDA pipeline."""
    types = _classify_columns(df)
    numeric = types["numeric"]
    categorical = types["categorical"]
    datetime_cols = types["datetime"]

    eda: dict[str, Any] = {
        "column_types": types,
        "summary_statistics": _summary_statistics(df, numeric),
        "missing_values": _missing_report(df),
        "correlation": _correlation_matrix(df, numeric),
        "outliers": _outliers_iqr(df, numeric),
        "categorical_frequency": _categorical_frequency(df, categorical),
        "trends": {},
    }

    if datetime_cols:
        # Use first datetime column for trend analysis
        eda["trends"] = _trend_for_datetime(df, datetime_cols[0], numeric)

    return _sanitize_for_json(eda)
