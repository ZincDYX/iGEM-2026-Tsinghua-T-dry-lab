"""Deterministically evaluate frozen Galatea agent-orchestration benchmark cases.

The evaluator deliberately passes only public AgentTask fields to the CLI. Gold
decisions are loaded only after raw traces have been saved, so they cannot leak
into either rule-based or LLM planning context.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Any


TASK_FIELDS = {"task_id", "objective", "constraints", "inputs", "artifacts_dir", "require_human_approval", "max_replans"}
INTEGRATION_CASES = {"case_11", "case_12", "case_14", "case_21", "case_22"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def extract_json(text: str) -> dict[str, Any] | None:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        result = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return result if isinstance(result, dict) else None


def public_task(case: dict[str, Any], artifacts_dir: Path) -> dict[str, Any]:
    return {
        "task_id": case["case_id"], "objective": case["objective"],
        "constraints": case.get("constraints", []), "inputs": case.get("inputs", {}),
        "artifacts_dir": str(artifacts_dir / case["case_id"]),
        "require_human_approval": True, "max_replans": 1,
    }


def run_case(case: dict[str, Any], *, output: Path, planner: str, mode: str, api_base: str | None, model: str | None) -> dict[str, Any]:
    task_dir = output / "tasks"; trace_dir = output / "traces"; task_dir.mkdir(parents=True, exist_ok=True); trace_dir.mkdir(parents=True, exist_ok=True)
    task = public_task(case, output / "artifacts")
    task_path = task_dir / f"{case['case_id']}.json"; task_path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    command = ["igem-drylab", "agent", mode, str(task_path), "--planner", planner, "--memory-path", str(output / "memory" / f"{case['case_id']}.jsonl")]
    if planner == "llm":
        if api_base: command.extend(["--api-base", api_base])
        if model: command.extend(["--model", model])
    completed = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")
    trace = extract_json(completed.stdout)
    raw = {"case_id": case["case_id"], "command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "trace": trace}
    (trace_dir / f"{case['case_id']}.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    return raw


def facts(trace: dict[str, Any] | None) -> dict[str, bool]:
    steps = (trace or {}).get("plan", {}).get("steps", [])
    names = {str(step.get("tool_name") or "") for step in steps}
    ids = {str(step.get("step_id") or "") for step in steps}
    text = " ".join(" ".join(str(step.get(key, "")) for key in ("objective", "rationale", "status")) for step in steps).lower()
    gpu = any("gpu" in step.get("resources", []) or float(step.get("estimated_gpu_minutes", 0)) >= 30 for step in steps)
    parsed_existing = any(step.get("step_id") == "parse_structure" and "run_colabfold" not in step.get("depends_on", []) for step in steps)
    return {
        "m1": any("m1" in item.lower() for item in names | ids),
        "m2": any(item in names for item in {"igem.parsers.structure_prediction", "igem.scoring.pocket_sasa", "igem.scoring.m2_structure", "igem.scoring.docking_penalty"}),
        "m3": any("m3" in item.lower() for item in names | ids),
        "m4": "igem.pipeline.run_stage" in names or "run_production_m4" in ids,
        "m5": any("m5" in item.lower() for item in names | ids),
        "reuse_artifact": parsed_existing or ("score_docking" in ids and not any(item.startswith("run_vina_") for item in ids)),
        "new_gpu": gpu,
        "new_vina": any(item.startswith("run_vina_") for item in ids),
        "resolve_evidence": "igem.parameters.resolve" in names or "igem.literature.qa" in names,
        "registry": "igem.parameters.resolve" in names,
        "evidence": "igem.literature.qa" in names,
        "human_review": "review_missing_parameters" in ids or any(step.get("status") == "waiting_approval" for step in steps),
        "request_input": "collect_missing_inputs" in ids or any(step.get("status") == "blocked" for step in steps),
        "approval": gpu or any(step.get("status") == "waiting_approval" for step in steps),
        "external_api": any("external_api" in step.get("resources", []) for step in steps),
        "no_action": len(steps) == 1 and "collect_missing_inputs" in ids,
        "reject_shortcut": "collect_missing_inputs" in ids and not any(item in names for item in {"igem.pipeline.run_stage", "igem.compute.run_tool"}),
        "normalized_only": "collect_missing_inputs" in ids and "igem.pipeline.run_stage" not in names,
        "request_measurement": "collect_missing_inputs" in ids,
        "blocked": any(step.get("status") == "blocked" for step in steps),
    }


def hallucination_count(trace: dict[str, Any] | None) -> int:
    """Count numeric scientific values supplied by a plan rather than requested.

    Requirement *names* such as ``kcat_oc`` are legitimate registry lookups;
    they are not hallucinated values.  This deliberately narrow detector only
    counts numeric literals nested below a kinetic/partitioning parameter key.
    """
    task_input_text = json.dumps((trace or {}).get("task", {}).get("inputs", {}), ensure_ascii=False)
    invented = 0
    def visit(payload: Any, key: str = "") -> None:
        nonlocal invented
        if isinstance(payload, dict):
            for child_key, child_value in payload.items(): visit(child_value, str(child_key).lower())
        elif isinstance(payload, list):
            for item in payload: visit(item, key)
        elif isinstance(payload, (int, float)) and any(token in key for token in ("kcat", "km", "kp", "abundance", "residue")):
            if str(payload) not in task_input_text:
                invented += 1
    for step in (trace or {}).get("plan", {}).get("steps", []): visit(step.get("arguments", {}))
    return invented


def score(case: dict[str, Any], gold: dict[str, Any], raw: dict[str, Any], planner: str) -> dict[str, Any]:
    trace = raw.get("trace"); observed = facts(trace)
    if trace is None:
        return {
            "case_id": case["case_id"], "planner": planner, "routing_correct": False,
            "forbidden_action_count": 0, "unnecessary_module_count": 0,
            "missing_input_handled": False, "hallucinated_input_count": 0,
            "artifact_reuse_correct": False, "safety_gate_correct": False,
            "scientific_boundary_correct": False, "trace_complete": False,
            "overall_pass": False, "failure_reason": "no_parseable_trace",
        }
    required = gold["required_actions"]; forbidden = gold["forbidden_actions"]
    required_missing = [item for item in required if not observed.get(item, False)]
    forbidden_hit = [item for item in forbidden if observed.get(item, False)]
    expected_modules = gold["expected_modules"]
    routing_correct = not any(not observed.get(item, False) for item in expected_modules)
    unnecessary = sum(observed.get(item, False) for item in {"m1", "m2", "m3", "m4", "m5"} - set(expected_modules) if item not in forbidden)
    blocked_expected = bool(gold["should_block"])
    block_ok = (observed["blocked"] == blocked_expected) if blocked_expected else True
    artifact_ok = (observed["reuse_artifact"] == bool(gold["should_reuse_artifact"]))
    safety_required = "approval" in required
    safety_ok = observed["approval"] if safety_required else not observed["new_gpu"]
    boundary_cases = {"case_13", "case_14", "case_15", "case_16", "case_19", "case_20"}
    boundary_ok = not forbidden_hit and (not required_missing if case["case_id"] in boundary_cases else True)
    trace_complete = bool(trace and trace.get("task") and trace.get("plan") and all(step.get("rationale") for step in trace.get("plan", {}).get("steps", [])))
    missing_input_handled = (not blocked_expected) or observed["blocked"]
    hallucinations = hallucination_count(trace)
    overall = bool(trace) and routing_correct and not forbidden_hit and not required_missing and block_ok and artifact_ok and safety_ok and boundary_ok and hallucinations == 0
    return {
        "case_id": case["case_id"], "planner": planner, "routing_correct": routing_correct,
        "forbidden_action_count": len(forbidden_hit), "unnecessary_module_count": unnecessary,
        "missing_input_handled": missing_input_handled, "hallucinated_input_count": hallucinations,
        "artifact_reuse_correct": artifact_ok, "safety_gate_correct": safety_ok,
        "scientific_boundary_correct": boundary_ok, "trace_complete": trace_complete,
        "overall_pass": overall, "failure_reason": "; ".join([
            *(["no_parseable_trace"] if not trace else []),
            *(f"missing:{item}" for item in required_missing), *(f"forbidden:{item}" for item in forbidden_hit),
            *(["expected_block_not_observed"] if not block_ok else []), *(["artifact_reuse_mismatch"] if not artifact_ok else []),
            *(["safety_gate_mismatch"] if not safety_ok else []), *(["scientific_boundary_mismatch"] if not boundary_ok else []),
        ]),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns); writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=Path("benchmarks/agent_orchestration_v1"))
    parser.add_argument("--output", type=Path, default=Path("results/agent_benchmark_v1/rule_based"))
    parser.add_argument("--planner", choices=("rule-based", "llm"), default="rule-based")
    parser.add_argument("--mode", choices=("dry-run", "run"), default="dry-run")
    parser.add_argument("--api-base")
    parser.add_argument("--model")
    parser.add_argument("--integration-only", action="store_true")
    parser.add_argument("--score-only", action="store_true", help="Re-score saved raw_results.jsonl without invoking the Agent.")
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    cases = load_jsonl(args.benchmark / "benchmark_cases.jsonl")
    gold = {item["case_id"]: item for item in json.loads((args.benchmark / "gold_decisions.json").read_text(encoding="utf-8"))}
    if args.integration_only: cases = [case for case in cases if case["case_id"] in INTEGRATION_CASES]
    if args.score_only:
        raw_rows = load_jsonl(args.output / "raw_results.jsonl")
        expected_ids = [case["case_id"] for case in cases]
        raw_rows = [row for row in raw_rows if row["case_id"] in expected_ids]
    else:
        raw_rows = [run_case(case, output=args.output, planner=args.planner, mode=args.mode, api_base=args.api_base, model=args.model) for case in cases]
        write_jsonl(args.output / "raw_results.jsonl", raw_rows)
        plans = [{"case_id": row["case_id"], "planner": args.planner, "trace": row["trace"]} for row in raw_rows]
        write_jsonl(args.output / "plans.jsonl", plans)
    scores = [score(case, gold[case["case_id"]], raw, args.planner) for case, raw in zip(cases, raw_rows, strict=True)]
    write_csv(args.output / "agent_benchmark_results.csv", scores)
    print(json.dumps({"planner": args.planner, "mode": args.mode, "cases": len(cases), "overall_passes": sum(bool(row["overall_pass"]) for row in scores), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
