from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


ALLOWED_EXTENSIONS = (".csv", ".xlsx", ".xls", ".xlsm")


def is_allowed_filename(filename: str | None) -> bool:
    if not filename:
        return False
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS)

