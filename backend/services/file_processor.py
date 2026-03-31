"""CSV/Excel ingestion and cleaning."""

from __future__ import annotations

import io
import warnings
from typing import Any

import pandas as pd


def _read_csv_bytes(data: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(data))


def _read_excel_bytes(data: bytes) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(data), engine="openpyxl")


def load_from_bytes(data: bytes, filename: str) -> pd.DataFrame:
    """Load a CSV or Excel file from raw bytes."""
    name = (filename or "").lower()
    if name.endswith(".csv"):
        return _read_csv_bytes(data)
    if name.endswith((".xlsx", ".xlsm")):
        return _read_excel_bytes(data)
    if name.endswith(".xls"):
        return pd.read_excel(io.BytesIO(data))
    # Guess by sniffing
    try:
        return _read_csv_bytes(data)
    except Exception:
        return _read_excel_bytes(data)


def _infer_better_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        s = out[col]
        if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
            coerced = pd.to_numeric(s, errors="coerce")
            if coerced.notna().sum() >= max(1, int(0.8 * len(s))):
                out[col] = coerced
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    dt = pd.to_datetime(s, errors="coerce", utc=False)
                if dt.notna().sum() >= max(1, int(0.5 * len(s))):
                    out[col] = dt
    return out


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates, handle missing values, and fix dtypes."""
    cleaned = df.copy()
    cleaned = cleaned.drop_duplicates()

    for col in cleaned.columns:
        s = cleaned[col]
        if pd.api.types.is_numeric_dtype(s):
            med = s.median()
            if pd.isna(med):
                cleaned[col] = s.fillna(0)
            else:
                cleaned[col] = s.fillna(med)
        elif pd.api.types.is_datetime64_any_dtype(s):
            cleaned[col] = s.ffill().bfill()
        else:
            mode = s.mode()
            fill = mode.iloc[0] if len(mode) else "Unknown"
            cleaned[col] = s.fillna(fill)

    cleaned = _infer_better_dtypes(cleaned)
    return cleaned


def dataset_overview(df: pd.DataFrame) -> dict[str, Any]:
    """Lightweight summary for upload response."""
    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": [
            {
                "name": str(c),
                "dtype": str(df[c].dtype),
            }
            for c in df.columns
        ],
    }
