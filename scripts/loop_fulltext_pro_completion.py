from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = Path(r"C:\Users\zhaol\Documents\Codex\2026-07-16\d-25-python-code")
DEFAULT_DB = ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_fulltext_pro_completed.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_fulltext_pro_completed_summary.json"
DEFAULT_LOOP_SUMMARY = ROOT / "essay" / "fulltext_pro_loop_completion_summary.json"
DEFAULT_LOOP_LOG = ROOT / "essay" / "fulltext_pro_loop_completion_log.csv"
FULLTEXT_SCRIPT = WORK_ROOT / "work" / "fulltext_pro_field_completion.py"
if str(FULLTEXT_SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(FULLTEXT_SCRIPT.parent))

import fulltext_pro_field_completion as ft

UNKNOWN = {"", "unknown", "none", "null", "nan", "n/a", "na", "not specified", "not available"}
LABEL_FIELDS = ["best_product_family", "best_canonical_product", "best_host_group", "best_canonical_host"]
TARGET_FIELDS = [
    "enzyme_name",
    "enzyme_mutant",
    "enzyme_source_species",
    "expression_host",
    "substrate_name",
    "main_product_name",
    "reaction_system_type",
    "is_whole_cell",
    "llps_component",
    "llps_state",
    "llps_trigger",
    "reaction_temperature",
    "reaction_ph",
    "reaction_time",
    "buffer_type",
    "substrate_concentration",
    "cofactor",
    "cofactor_concentration",
    "cosubstrate",
    "cell_density_od600",
]


PROFILES = [
    {
        "name": "unattempted_all_compact",
        "mode": "all_missing_fields",
        "include_attempted": False,
        "rows_per_batch": 12,
        "limit": 20,
        "max_context_chars": 14000,
        "max_text_files": 4,
        "note": "- Prefer direct paragraph/table contexts around the row numeric value. Fill all directly supported missing fields.",
    },
    {
        "name": "unattempted_product_wide",
        "mode": "missing_products",
        "include_attempted": False,
        "rows_per_batch": 10,
        "limit": 18,
        "max_context_chars": 24000,
        "max_text_files": 7,
        "note": "- Focus especially on product identity and product family. Search table titles, captions, abstract, results, and supplementary table context for the product linked to each numeric result.",
    },
    {
        "name": "unattempted_host_system_wide",
        "mode": "missing_hosts",
        "include_attempted": False,
        "rows_per_batch": 10,
        "limit": 18,
        "max_context_chars": 22000,
        "max_text_files": 7,
        "note": "- Focus especially on expression host, strain, cell-free versus whole-cell system, and reaction system type linked to each numeric result.",
    },
    {
        "name": "retry_missing_labels_widest",
        "mode": "missing_labels",
        "include_attempted": True,
        "rows_per_batch": 8,
        "limit": 12,
        "max_context_chars": 32000,
        "max_text_files": 10,
        "note": "- This is a retry pass. Re-check all supplied fulltext/SI contexts, including broad article-level cues, but only fill labels when evidence supports the row result. If multiple products or hosts conflict, keep null.",
    },
]

UNTIL_ALL_PROFILE = {
    "name": "until_all_unattempted_fulltext",
    "mode": "all_missing_fields",
    "include_attempted": False,
    "rows_per_batch": 16,
    "limit": 35,
    "max_context_chars": 12000,
    "max_text_files": 4,
    "note": "- This is an exhaustive first-attempt pass. For each row with missing fields, search the retrieved fulltext/SI context and fill every directly supported field. If not supported, return null so the row is marked attempted.",
}


def is_unknown(value: object) -> bool:
    return str(value or "").strip().lower() in UNKNOWN


def count_state(csv_path: Path) -> dict[str, int]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    state: dict[str, int] = {"rows": len(rows)}
    for field in LABEL_FIELDS:
        state[f"{field}_unknown"] = sum(1 for row in rows if is_unknown(row.get(field)))
    for field in TARGET_FIELDS:
        state[f"{field}_filled_by_pro"] = sum(
            1
            for row in rows
            if row.get(f"best_{field}_source") == "fulltext_pro"
            and not is_unknown(row.get(f"best_{field}_value"))
        )
    state["accepted"] = sum(1 for row in rows if row.get("fulltext_pro_status") == "accepted")
    state["low_confidence"] = sum(1 for row in rows if row.get("fulltext_pro_status") == "low_confidence")
    state["error"] = sum(1 for row in rows if row.get("fulltext_pro_status") == "error")
    state["unattempted"] = sum(1 for row in rows if is_unknown(row.get("fulltext_pro_status")))
    return state


def count_eligible_unattempted(csv_path: Path, rows_per_batch: int) -> dict[str, int]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        ft.initialize_best_columns(row)
    text_map = ft.load_text_manifests(ft.ROOT)
    batches = ft.build_row_batches(
        rows,
        text_map,
        max(1, rows_per_batch),
        0,
        "all_missing_fields",
        only_unattempted=True,
    )
    return {
        "eligible_unattempted_rows": sum(len(batch["rows"]) for batch in batches),
        "eligible_unattempted_batches": len(batches),
        "eligible_unattempted_dois": len({batch["doi"] for batch in batches}),
    }


def improvement(before: dict[str, int], after: dict[str, int]) -> int:
    label_gain = sum(before[f"{field}_unknown"] - after[f"{field}_unknown"] for field in LABEL_FIELDS)
    field_gain = sum(after[f"{field}_filled_by_pro"] - before[f"{field}_filled_by_pro"] for field in TARGET_FIELDS)
    accepted_gain = after["accepted"] - before["accepted"]
    return max(0, label_gain) + max(0, field_gain) + max(0, accepted_gain)


def append_log(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    fields = [
        "timestamp", "pass_index", "profile", "elapsed_sec", "return_code", "gain",
        "product_family_unknown", "canonical_product_unknown", "host_group_unknown", "canonical_host_unknown",
        "accepted", "low_confidence", "error", "unattempted",
    ]
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def run_profile(args: argparse.Namespace, profile: dict[str, object], pass_index: int) -> tuple[int, float]:
    retry_tag = f"loop-{profile['name']}-pass-{pass_index}-{int(time.time())}"
    cmd = [
        sys.executable,
        str(FULLTEXT_SCRIPT),
        "--input", str(args.db),
        "--output", str(args.db),
        "--summary", str(args.summary),
        "--mode", str(profile["mode"]),
        "--limit", str(profile["limit"]),
        "--rows-per-batch", str(profile["rows_per_batch"]),
        "--workers", str(args.workers),
        "--max-context-chars", str(profile["max_context_chars"]),
        "--max-text-files", str(profile["max_text_files"]),
        "--checkpoint-every", str(args.checkpoint_every),
        "--model", args.model,
        "--retry-tag", retry_tag,
        "--strategy-note", str(profile["note"]),
    ]
    if profile["include_attempted"]:
        cmd.append("--include-attempted")
    start = time.time()
    completed = subprocess.run(cmd, cwd=str(WORK_ROOT), text=True)
    return completed.returncode, time.time() - start


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--loop-summary", type=Path, default=DEFAULT_LOOP_SUMMARY)
    parser.add_argument("--loop-log", type=Path, default=DEFAULT_LOOP_LOG)
    parser.add_argument("--max-passes", type=int, default=4)
    parser.add_argument("--min-gain", type=int, default=5)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--until-all-attempted", action="store_true")
    parser.add_argument("--until-pass-limit", type=int, default=35)
    parser.add_argument("--until-rows-per-batch", type=int, default=16)
    args = parser.parse_args()
    UNTIL_ALL_PROFILE["limit"] = args.until_pass_limit
    UNTIL_ALL_PROFILE["rows_per_batch"] = args.until_rows_per_batch

    before_all = count_state(args.db)
    pass_results = []
    stale_passes = 0
    for i in range(1, args.max_passes + 1):
        if args.until_all_attempted:
            eligible = count_eligible_unattempted(args.db, int(UNTIL_ALL_PROFILE["rows_per_batch"]))
            if eligible["eligible_unattempted_rows"] <= 0:
                print("All eligible unattempted rows have been attempted; stopping.", flush=True)
                break
            profile = dict(UNTIL_ALL_PROFILE)
        else:
            eligible = {}
            profile = PROFILES[(i - 1) % len(PROFILES)]
        before = count_state(args.db)
        print(f"loop_pass={i}/{args.max_passes} profile={profile['name']} before_unattempted={before['unattempted']} eligible={eligible}", flush=True)
        code, elapsed = run_profile(args, profile, i)
        after = count_state(args.db)
        gain = improvement(before, after)
        log_row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "pass_index": i,
            "profile": profile["name"],
            "elapsed_sec": round(elapsed, 1),
            "return_code": code,
            "gain": gain,
            "product_family_unknown": after["best_product_family_unknown"],
            "canonical_product_unknown": after["best_canonical_product_unknown"],
            "host_group_unknown": after["best_host_group_unknown"],
            "canonical_host_unknown": after["best_canonical_host_unknown"],
            "accepted": after["accepted"],
            "low_confidence": after["low_confidence"],
            "error": after["error"],
            "unattempted": after["unattempted"],
        }
        log_row.update(eligible)
        append_log(args.loop_log, log_row)
        pass_results.append(log_row)
        print(json.dumps(log_row, ensure_ascii=False), flush=True)
        if code != 0:
            break
        if gain < args.min_gain:
            stale_passes += 1
        else:
            stale_passes = 0
        if not args.until_all_attempted and stale_passes >= len(PROFILES):
            print("No meaningful progress after a full strategy cycle; stopping.", flush=True)
            break

    after_all = count_state(args.db)
    final_eligible = count_eligible_unattempted(args.db, int(UNTIL_ALL_PROFILE["rows_per_batch"]))
    summary = {
        "started_state": before_all,
        "final_state": after_all,
        "final_eligible_unattempted": final_eligible,
        "total_gain": improvement(before_all, after_all),
        "passes": pass_results,
        "db": str(args.db),
        "loop_log": str(args.loop_log),
    }
    args.loop_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary["final_state"], ensure_ascii=False), flush=True)
    print(f"Wrote: {args.loop_summary}", flush=True)
    print(f"Wrote: {args.loop_log}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
