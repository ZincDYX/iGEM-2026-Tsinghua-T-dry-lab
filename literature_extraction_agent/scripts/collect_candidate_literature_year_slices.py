from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import time
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def load_base_module():
    path = ROOT / "scripts" / "collect_candidate_literature_20000.py"
    spec = importlib.util.spec_from_file_location("collect_candidate_literature_20000_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_module()
SCOPUS_ENDPOINT = base.SCOPUS_ENDPOINT


def seed_records(seed_paths: list[Path]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in seed_paths:
        if not path.exists() or path.stat().st_size == 0:
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                key = row.get("dedupe_key") or base.dedupe_key(row.get("doi", ""), row.get("title", ""))
                if key and key not in records:
                    records[key] = dict(row)
        if records:
            break
    return records


def default_state(year_start: int, year_end: int) -> dict[str, Any]:
    tasks = []
    for group in base.KEYWORD_GROUPS:
        for year in range(year_start, year_end - 1, -1):
            tasks.append({
                "source": "scopus_year",
                "group": group["label"],
                "year": year,
                "start": 0,
                "count": 25,
                "done": False,
                "total": None,
                "pages": 0,
            })
    return {"tasks": tasks, "raw_seen": 0}


def save_outputs(records: dict[str, dict[str, Any]], state: dict[str, Any], *, target: int, prefix: str) -> None:
    csv_path = OUT / f"{prefix}.csv"
    jsonl_path = OUT / f"{prefix}.jsonl"
    state_path = OUT / f"{prefix}_state.json"
    summary_path = OUT / f"{prefix}_summary.json"
    rows = list(records.values())[:target]
    for idx, row in enumerate(rows, start=1):
        row["candidate_id"] = idx
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=base.COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "target": target,
        "unique_candidates": len(rows),
        "raw_seen": state.get("raw_seen", 0),
        "active_tasks": sum(1 for t in state["tasks"] if not t.get("done")),
        "tasks_total": len(state["tasks"]),
        "tasks_done": sum(1 for t in state["tasks"] if t.get("done")),
        "csv": str(csv_path),
        "jsonl": str(jsonl_path),
        "state": str(state_path),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=50000)
    parser.add_argument("--prefix", default="candidate_literature_50000_year_slices")
    parser.add_argument("--seed-prefix", default="candidate_literature_50000")
    parser.add_argument("--year-start", type=int, default=2026)
    parser.add_argument("--year-end", type=int, default=1990)
    parser.add_argument("--max-requests", type=int, default=800)
    args = parser.parse_args()

    base.ROOT = ROOT
    base.OUT = OUT
    base.API_TXT = ROOT / "API.txt"
    elsevier_key, _ = base.parse_keys()

    seed_paths = [
        OUT / f"{args.prefix}.csv",
        OUT / f"{args.seed_prefix}.csv",
        OUT / "candidate_literature_20000.csv",
    ]
    records = seed_records(seed_paths)
    state_path = OUT / f"{args.prefix}_state.json"
    if state_path.exists() and state_path.stat().st_size:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        state = default_state(args.year_start, args.year_end)

    group_by_label = {g["label"]: g for g in base.KEYWORD_GROUPS}
    session = requests.Session()
    requests_done = 0
    while len(records) < args.target and any(not t.get("done") for t in state["tasks"]) and requests_done < args.max_requests:
        for task in state["tasks"]:
            if len(records) >= args.target or requests_done >= args.max_requests:
                break
            if task.get("done"):
                continue
            group = group_by_label[task["group"]]
            query = f'TITLE-ABS-KEY({group["query"]}) AND PUBYEAR = {task["year"]}'
            try:
                js = base.request_json(
                    session,
                    SCOPUS_ENDPOINT,
                    headers={"X-ELS-APIKey": elsevier_key, "Accept": "application/json"},
                    params={"query": query, "count": task["count"], "start": task["start"]},
                )
                sr = js.get("search-results", {})
                task["total"] = int(sr.get("opensearch:totalResults") or 0)
                entries = sr.get("entry") or []
                if not entries:
                    task["done"] = True
                for entry in entries:
                    if isinstance(entry, dict) and entry.get("dc:title"):
                        base.add_record(records, base.parse_scopus(entry, group))
                        state["raw_seen"] = state.get("raw_seen", 0) + 1
                task["start"] += len(entries)
                task["pages"] += 1
                # Scopus search windows usually stop around start=5000.
                if task["start"] >= task["total"] or task["start"] >= 5000 or len(entries) < task["count"]:
                    task["done"] = True
                requests_done += 1
                if requests_done % 25 == 0:
                    save_outputs(records, state, target=args.target, prefix=args.prefix)
                    print(
                        f"progress unique={len(records)} requests={requests_done} "
                        f"active={sum(1 for t in state['tasks'] if not t.get('done'))}",
                        flush=True,
                    )
                time.sleep(0.05)
            except Exception as exc:
                task["last_error"] = str(exc)
                # If a year slice still exceeds Scopus window or has syntax trouble, move on.
                task["done"] = True
                requests_done += 1
    save_outputs(records, state, target=args.target, prefix=args.prefix)
    summary = json.loads((OUT / f"{args.prefix}_summary.json").read_text(encoding="utf-8"))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
