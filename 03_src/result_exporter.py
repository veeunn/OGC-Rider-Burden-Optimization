"""Result serialization helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Any
import csv
import json


def write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def write_rows_csv(path: str | Path, rows: Iterable[Mapping[str, Any]]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError("No rows supplied.")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
