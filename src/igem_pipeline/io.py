import json
from pathlib import Path
from typing import Iterable, Optional, TypeVar

import pandas as pd
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_fasta(path: Path) -> dict[str, str]:
    records: dict[str, list[str]] = {}
    current_id: Optional[str] = None
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                current_id = line[1:].split()[0]
                records[current_id] = []
            elif current_id is None:
                raise ValueError(f"FASTA sequence found before header in {path}")
            else:
                records[current_id].append(line)
    return {name: "".join(parts) for name, parts in records.items()}


def write_models(stage_dir: Path, stem: str, records: Iterable[BaseModel]) -> None:
    ensure_dir(stage_dir)
    payload = [record.model_dump(mode="json") for record in records]
    json_path = stage_dir / f"{stem}.json"
    csv_path = stage_dir / f"{stem}.csv"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame(payload).to_csv(csv_path, index=False)
