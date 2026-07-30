from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_fasta(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    current_id: str | None = None
    chunks: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_id is not None:
                    records[current_id] = "".join(chunks)
                current_id = line[1:].split()[0]
                chunks = []
            else:
                chunks.append(line)
    if current_id is not None:
        records[current_id] = "".join(chunks)
    if not records:
        raise ValueError(f"No FASTA records found in {path}")
    return records


def write_models(directory: Path, stem: str, records: Iterable[BaseModel]) -> None:
    ensure_dir(directory)
    items = list(records)
    payload = [item.model_dump(mode="json") for item in items]
    (directory / f"{stem}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if not items:
        (directory / f"{stem}.csv").write_text("", encoding="utf-8")
        return
    fields = list(payload[0])
    with (directory / f"{stem}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(payload)
