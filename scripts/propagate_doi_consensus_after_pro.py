from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


UNKNOWN = {"", "unknown", "none", "null", "nan", "n/a", "na", "not specified", "not available", "unidentified"}

CONSENSUS_FIELDS = [
    "best_canonical_product",
    "best_product_family",
    "best_canonical_host",
    "best_host_group",
    "best_enzyme_name_value",
    "best_enzyme_source_species_value",
    "best_expression_host_value",
    "best_substrate_name_value",
    "best_main_product_name_value",
    "best_reaction_system_type_value",
    "best_is_whole_cell_value",
    "best_llps_state_value",
    "best_llps_trigger_value",
]


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def is_unknown(value: Any) -> bool:
    return compact(value).lower() in UNKNOWN


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def evidence_for(row: dict[str, str], field: str) -> str:
    if field in {"best_canonical_product", "best_product_family"}:
        candidates = ["best_main_product_name_evidence", "main_product_name_evidence", "primary_result_evidence", "title_clean"]
    elif field in {"best_canonical_host", "best_host_group", "best_expression_host_value"}:
        candidates = ["best_expression_host_evidence", "expression_host_evidence", "primary_result_evidence", "title_clean"]
    elif field == "best_enzyme_name_value":
        candidates = ["best_enzyme_name_evidence", "enzyme_name_evidence", "primary_result_evidence", "title_clean"]
    elif field == "best_enzyme_source_species_value":
        candidates = ["best_enzyme_source_species_evidence", "enzyme_source_species_evidence", "primary_result_evidence", "title_clean"]
    elif field == "best_substrate_name_value":
        candidates = ["best_substrate_name_evidence", "substrate_name_evidence", "primary_result_evidence", "title_clean"]
    elif field == "best_main_product_name_value":
        candidates = ["best_main_product_name_evidence", "main_product_name_evidence", "primary_result_evidence", "title_clean"]
    elif field in {"best_llps_state_value", "best_llps_trigger_value"}:
        candidates = ["best_llps_state_evidence", "best_llps_trigger_evidence", "llps_state_evidence", "llps_trigger_evidence", "primary_result_evidence", "title_clean"]
    else:
        candidates = ["best_reaction_system_type_evidence", "reaction_system_type_evidence", "primary_result_evidence", "title_clean"]
    for key in candidates:
        text = compact(row.get(key))
        if text and not is_unknown(text):
            return text[:360]
    return "DOI-level consensus from other records in the same paper."


def append_evidence(old: str, field: str, evidence: str) -> str:
    piece = f"{field}: DOI-level consensus after Pro/SI backfill; evidence={compact(evidence)[:220]}"
    if not old:
        return piece
    if piece in old:
        return old
    return (old + " || " + piece)[:1600]


def build_consensus(rows: list[dict[str, str]]) -> dict[str, dict[str, tuple[str, str, int, int]]]:
    by_doi: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        doi = compact(row.get("doi")).lower()
        if doi:
            by_doi[doi].append(row)

    consensus: dict[str, dict[str, tuple[str, str, int, int]]] = {}
    for doi, items in by_doi.items():
        field_map: dict[str, tuple[str, str, int, int]] = {}
        for field in CONSENSUS_FIELDS:
            vals = [compact(row.get(field)) for row in items if not is_unknown(row.get(field))]
            if not vals:
                continue
            counts = Counter(vals)
            top, n = counts.most_common(1)[0]
            # Conservative propagation: only use article-level consensus when all observed
            # non-empty values agree, or when a dominant value appears repeatedly.
            if len(counts) == 1 or (n >= 3 and n / len(vals) >= 0.85):
                source_row = next(row for row in items if compact(row.get(field)) == top)
                field_map[field] = (top, evidence_for(source_row, field), n, len(vals))
        if field_map:
            consensus[doi] = field_map
    return consensus


def count_unknowns(rows: list[dict[str, str]]) -> dict[str, int]:
    return {field: sum(1 for row in rows if is_unknown(row.get(field))) for field in CONSENSUS_FIELDS}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    rows = read_csv(args.input)
    before = count_unknowns(rows)
    consensus = build_consensus(rows)
    changes: Counter[str] = Counter()
    changed_rows = 0

    for row in rows:
        doi = compact(row.get("doi")).lower()
        if not doi or doi not in consensus:
            continue
        touched = False
        for field, (value, evidence, n, total) in consensus[doi].items():
            if field not in row or not is_unknown(row.get(field)):
                continue
            row[field] = value
            source_field = f"{field}_source"
            if source_field in row:
                row[source_field] = f"doi_consensus_after_pro:{n}/{total}"
            evidence_field = f"{field}_evidence"
            if evidence_field in row and is_unknown(row.get(evidence_field)):
                row[evidence_field] = evidence
            row["si_rule_backfill_status"] = "updated"
            row["si_rule_backfill_evidence"] = append_evidence(row.get("si_rule_backfill_evidence", ""), field, evidence)
            methods = set(filter(None, compact(row.get("si_rule_backfill_methods")).split(";")))
            methods.add("doi_consensus_after_pro")
            row["si_rule_backfill_methods"] = ";".join(sorted(methods))
            changes[field] += 1
            touched = True
        if touched:
            changed_rows += 1

    after = count_unknowns(rows)
    write_csv(args.output, rows)
    summary = {
        "input": str(args.input),
        "output": str(args.output),
        "rows": len(rows),
        "consensus_dois": len(consensus),
        "changed_rows": changed_rows,
        "changes_by_field": dict(changes.most_common()),
        "unknown_before": before,
        "unknown_after": after,
        "unknown_reduction": {field: before[field] - after[field] for field in before},
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
