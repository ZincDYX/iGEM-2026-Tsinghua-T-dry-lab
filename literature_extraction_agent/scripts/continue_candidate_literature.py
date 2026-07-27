from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import collect_candidate_literature_20000 as base


def seed_if_needed(prefix: str) -> None:
    out = ROOT / "outputs"
    target_csv = out / f"{prefix}.csv"
    target_jsonl = out / f"{prefix}.jsonl"
    target_state = out / f"{prefix}_state.json"
    source_csv = out / "candidate_literature_20000.csv"
    source_jsonl = out / "candidate_literature_20000.jsonl"
    source_state = out / "candidate_literature_20000_state.json"

    if not target_csv.exists() and source_csv.exists():
        shutil.copy2(source_csv, target_csv)
    if not target_jsonl.exists() and source_jsonl.exists():
        shutil.copy2(source_jsonl, target_jsonl)
    if not target_state.exists() and source_state.exists():
        shutil.copy2(source_state, target_state)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=50000)
    parser.add_argument("--prefix", default="candidate_literature_50000")
    parser.add_argument("--max-requests", type=int, default=1200)
    args = parser.parse_args()

    seed_if_needed(args.prefix)

    out = ROOT / "outputs"
    base.ROOT = ROOT
    base.OUT = out
    base.API_TXT = ROOT / "API.txt"
    base.TARGET = int(args.target)
    base.CSV_PATH = out / f"{args.prefix}.csv"
    base.JSONL_PATH = out / f"{args.prefix}.jsonl"
    base.STATE_PATH = out / f"{args.prefix}_state.json"
    base.SUMMARY_PATH = out / f"{args.prefix}_summary.json"

    base.main(max_requests=int(args.max_requests))
    summary = json.loads(base.SUMMARY_PATH.read_text(encoding="utf-8"))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
