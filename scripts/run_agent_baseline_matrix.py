"""Run a fair provider/architecture matrix on one frozen Agent benchmark."""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BaselineProfile:
    name: str
    planner: str
    provider: str
    api_key_env: str | None = None
    api_base_env: str | None = None
    model_env: str | None = None


PROFILES = {
    item.name: item
    for item in (
        BaselineProfile("rule_based", "rule-based", "local"),
        BaselineProfile("qwen", "llm", "qwen", "QWEN_API_KEY", "QWEN_API_BASE", "QWEN_MODEL"),
        BaselineProfile("deepseek", "llm", "deepseek", "DEEPSEEK_API_KEY", "DEEPSEEK_API_BASE", "DEEPSEEK_MODEL"),
        BaselineProfile("hybrid_qwen", "hybrid", "qwen", "QWEN_API_KEY", "QWEN_API_BASE", "QWEN_MODEL"),
        BaselineProfile("hybrid_deepseek", "hybrid", "deepseek", "DEEPSEEK_API_KEY", "DEEPSEEK_API_BASE", "DEEPSEEK_MODEL"),
    )
}

QUALITY_FIELDS = (
    "routing_correct",
    "missing_input_handled",
    "artifact_reuse_correct",
    "safety_gate_correct",
    "scientific_boundary_correct",
    "trace_complete",
    "overall_pass",
)


def load_env(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def numeric(row: dict[str, str], key: str) -> float | None:
    try:
        return float(row.get(key, ""))
    except (TypeError, ValueError):
        return None


def summarize(name: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    elapsed = [value for row in rows if (value := numeric(row, "elapsed_seconds")) is not None]
    total_tokens = [value for row in rows if (value := numeric(row, "total_tokens")) is not None]
    summary: dict[str, Any] = {
        "baseline": name,
        "planner": rows[0].get("planner", "") if rows else "",
        "provider": rows[0].get("provider", "") if rows else "",
        "model": rows[0].get("model", "") if rows else "",
        "cases": len(rows),
    }
    for field in QUALITY_FIELDS:
        summary[field] = round(sum(row.get(field) == "True" for row in rows) / len(rows), 4) if rows else 0.0
    summary.update({
        "forbidden_action_rate": round(sum(int(row.get("forbidden_action_count", 0)) > 0 for row in rows) / len(rows), 4) if rows else 0.0,
        "hallucinated_input_rate": round(sum(int(row.get("hallucinated_input_count", 0)) > 0 for row in rows) / len(rows), 4) if rows else 0.0,
        "schema_first_pass_rate": round(sum(row.get("schema_valid_first_attempt") == "True" for row in rows) / len(rows), 4) if rows else 0.0,
        "mean_elapsed_seconds": round(statistics.fmean(elapsed), 4) if elapsed else "",
        "median_elapsed_seconds": round(statistics.median(elapsed), 4) if elapsed else "",
        "total_tokens": int(sum(total_tokens)) if total_tokens else "",
    })
    return summary


def profile_command(args: argparse.Namespace, profile: BaselineProfile, output: Path) -> list[str]:
    command = [
        sys.executable,
        "scripts/evaluate_agent_benchmark.py",
        "--benchmark", str(args.benchmark),
        "--output", str(output),
        "--planner", profile.planner,
        "--provider", profile.provider,
        "--label", profile.name,
        "--mode", args.mode,
        "--jobs", str(args.jobs),
    ]
    if args.case_ids:
        command.extend(["--case-ids", args.case_ids])
    if args.score_only:
        command.append("--score-only")
    if profile.api_key_env:
        command.extend(["--api-key-env", profile.api_key_env])
    api_base = os.getenv(profile.api_base_env or "") if profile.api_base_env else None
    model = os.getenv(profile.model_env or "") if profile.model_env else None
    if profile.provider == "deepseek":
        api_base = api_base or "https://api.deepseek.com/chat/completions"
        model = model or "deepseek-chat"
    if api_base:
        command.extend(["--api-base", api_base])
    if model:
        command.extend(["--model", model])
    return command


def profile_available(profile: BaselineProfile, *, score_only: bool) -> tuple[bool, str]:
    if profile.planner == "rule-based" or score_only:
        return True, "available"
    if not os.getenv(profile.api_key_env or ""):
        return False, f"missing {profile.api_key_env}"
    if profile.provider == "qwen" and not os.getenv(profile.api_base_env or ""):
        return False, f"missing {profile.api_base_env}"
    return True, "available"


def write_report(path: Path, summaries: list[dict[str, Any]], skipped: list[dict[str, str]], benchmark: Path) -> None:
    header = "| Baseline | Planner | Provider/model | Routing | Safety | Boundary | Overall | Hallucination | Mean s | Tokens |\n|---|---|---|---:|---:|---:|---:|---:|---:|---:|"
    body = "\n".join(
        f"| {row['baseline']} | {row['planner']} | {row['provider']}/{row['model']} | {row['routing_correct']:.3f} | {row['safety_gate_correct']:.3f} | {row['scientific_boundary_correct']:.3f} | {row['overall_pass']:.3f} | {row['hallucinated_input_rate']:.3f} | {row['mean_elapsed_seconds']} | {row['total_tokens']} |"
        for row in summaries
    )
    skipped_text = "\n".join(f"- `{item['baseline']}`: {item['reason']}" for item in skipped) or "- None"
    path.write_text(
        f"""# Agent baseline matrix

All profiles use the same frozen benchmark `{benchmark}`, public task fields, gold labels, execution mode, concurrency, and scorer. Gold decisions are read only after traces are saved.

{header}
{body}

## Skipped profiles

{skipped_text}

This benchmark evaluates orchestration, schema compliance, safety, and scientific-boundary preservation. It does not compare biological prediction accuracy. Hybrid profiles give the LLM semantic classification only; deterministic code owns stage/tool compilation.
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=Path("benchmarks/agent_orchestration_heldout_v2"))
    parser.add_argument("--output-root", type=Path, default=Path("results/agent_baseline_matrix"))
    parser.add_argument("--profiles", default=",".join(PROFILES), help="Comma-separated profile names.")
    parser.add_argument("--mode", choices=("dry-run", "run"), default="dry-run")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--case-ids")
    parser.add_argument("--score-only", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Fail instead of skipping an unconfigured provider.")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    load_env(args.env_file)
    selected_names = [item.strip() for item in args.profiles.split(",") if item.strip()]
    unknown = [name for name in selected_names if name not in PROFILES]
    if unknown:
        raise ValueError(f"Unknown profiles: {', '.join(unknown)}")
    if args.jobs < 1:
        raise ValueError("--jobs must be at least 1")

    args.output_root.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    combined_rows: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for name in selected_names:
        profile = PROFILES[name]
        available, reason = profile_available(profile, score_only=args.score_only)
        if not available:
            if args.strict:
                raise RuntimeError(f"{name}: {reason}")
            skipped.append({"baseline": name, "reason": reason})
            continue
        output = args.output_root / name
        completed = subprocess.run(profile_command(args, profile, output), text=True)
        if completed.returncode:
            if args.strict:
                raise RuntimeError(f"Baseline {name} failed with exit code {completed.returncode}")
            skipped.append({"baseline": name, "reason": f"evaluator exit code {completed.returncode}"})
            continue
        rows = read_rows(output / "agent_benchmark_results.csv")
        summaries.append(summarize(name, rows))
        combined_rows.extend(rows)

    write_rows(args.output_root / "baseline_matrix_summary.csv", summaries)
    write_rows(args.output_root / "baseline_matrix_case_results.csv", combined_rows)
    (args.output_root / "baseline_matrix_summary.json").write_text(json.dumps({"benchmark": str(args.benchmark), "summaries": summaries, "skipped": skipped}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(args.output_root / "AGENT_BASELINE_MATRIX_REPORT.md", summaries, skipped, args.benchmark)
    print(json.dumps({"profiles_completed": [row["baseline"] for row in summaries], "skipped": skipped, "output": str(args.output_root)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
