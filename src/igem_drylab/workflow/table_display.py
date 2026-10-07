"""Bounded original-string tables; no inferred roles, units or numerical conversion."""
import csv
import json
from typing import Literal

from .models import Contract, WorkflowError
from .display_resources import ResourceIdentity, MAX_POINTS


class TablePage(Contract):
    schema_version: Literal["display-table-v1"] = "display-table-v1"
    identity: ResourceIdentity
    offset: int
    total: int
    has_more: bool
    columns: list[str]
    rows: list[list[str | None]]
    text: str | None = None


def table_page(resources, project_id, file_id, offset, limit):
    path, identity, _ = resources.source(project_id, file_id)
    parsed = resources.boundary.check_original(path)
    columns, rows, text = [], [], None
    if path.suffix.lower() in {".csv", ".tsv"}:
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, delimiter="\t" if path.suffix.lower() == ".tsv" else ",")
            columns = next(reader, [])
            if not columns or len(columns) > 128 or len(set(columns)) != len(columns) or any(not c for c in columns):
                raise WorkflowError("table_columns_missing_or_duplicate")
            total = 0
            for row in reader:
                if len(row) != len(columns) or total >= MAX_POINTS:
                    raise WorkflowError("table_row_budget_or_shape_invalid")
                if offset <= total < offset + limit:
                    rows.append(row)
                total += 1
    elif path.suffix.lower() in {".json", ".yaml", ".yml", ".txt"}:
        raw = json.dumps(parsed, ensure_ascii=False, indent=2) if parsed is not None else path.read_text(encoding="utf-8-sig")
        total = len(raw)
        text = raw[offset:offset + limit]
    else:
        raise WorkflowError("unsupported_table_display_format")
    result = TablePage(identity=identity, offset=offset, total=total,
                       has_more=offset + (len(rows) if columns else len(text or "")) < total,
                       columns=columns, rows=rows, text=text).model_dump(mode="json")
    resources.boundary.check(result)
    return result
