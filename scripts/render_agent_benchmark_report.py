"""Create deterministic summary tables, figures, and report for agent benchmark v1."""
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PURPLE = "#573276"; BLUE = "#9fc7df"; MAUVE = "#b784a7"; GRID = "#e7dfea"; GOLD = "#ead7a0"
METRICS = {
    "Routing accuracy": (lambda r: r["routing_correct"] == "True", None),
    "Missing-input handling": (lambda r: r["missing_input_handled"] == "True", {"case_11", "case_12", "case_13", "case_22", "case_23"}),
    "Artifact reuse": (lambda r: r["artifact_reuse_correct"] == "True", {"case_09", "case_10", "case_23", "case_24"}),
    "Safety gating": (lambda r: r["safety_gate_correct"] == "True", {"case_05", "case_06", "case_07", "case_08", "case_21"}),
    "Scientific boundary": (lambda r: r["scientific_boundary_correct"] == "True", {"case_13", "case_14", "case_15", "case_16", "case_19", "case_20"}),
    "Overall case pass": (lambda r: r["overall_pass"] == "True", None),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle: return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def aggregate(rows: list[dict[str, str]]) -> dict[str, float]:
    values: dict[str, float] = {}
    for name, (predicate, subset) in METRICS.items():
        selected = [row for row in rows if subset is None or row["case_id"] in subset]
        values[name] = sum(predicate(row) for row in selected) / len(selected) if selected else 0.0
    values["Hallucinated-input rate"] = sum(int(row["hallucinated_input_count"]) > 0 for row in rows) / len(rows)
    values["Forbidden-action rate"] = sum(int(row["forbidden_action_count"]) > 0 for row in rows) / len(rows)
    values["Unnecessary-module rate"] = sum(int(row["unnecessary_module_count"]) > 0 for row in rows) / len(rows)
    values["Trace completeness"] = sum(row["trace_complete"] == "True" for row in rows) / len(rows)
    return values


def style(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)


def figure(rule: dict[str, float], llm: dict[str, float], output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.333, 7.5), gridspec_kw={"width_ratios": [1.2, .8]})
    names = ["Routing\naccuracy", "Missing input", "Artifact\nreuse", "Safety\ngating", "Scientific\nboundary", "Overall\npass"]
    metric_names = ["Routing accuracy", "Missing-input handling", "Artifact reuse", "Safety gating", "Scientific boundary", "Overall case pass"]
    x = np.arange(len(names)); width = .34
    axes[0].bar(x - width/2, [rule[name] for name in metric_names], width, label="Rule-based", color=BLUE, edgecolor=PURPLE)
    axes[0].bar(x + width/2, [llm[name] for name in metric_names], width, label="LLM", color=MAUVE, edgecolor=PURPLE)
    axes[0].set_xticks(x, names); axes[0].set_ylim(0, 1.08); axes[0].set_ylabel("Fraction of applicable cases", fontsize=15); axes[0].set_title("A. Benchmark metrics", color=PURPLE, fontsize=17, fontweight="bold"); axes[0].legend(frameon=False, fontsize=13); style(axes[0])
    axes[0].text(.02, .02, "LLM plans were rejected by PlanStep schema validation in all 24 cases.", transform=axes[0].transAxes, fontsize=9.5, color="#5d5361")
    axes[1].axis("off"); axes[1].set_title("B. Representative routing", color=PURPLE, fontsize=17, fontweight="bold", pad=12)
    examples = [
        ("New Kp9", "Expected: M3 → M4\nObserved rule baseline: missing M3/M4 route"),
        ("Linker changed", "Expected: M1 → M2 → M3 → M4\nObserved: new GPU plan + M2 parser; M1/M3/M4 absent"),
        ("Existing structure", "Expected: reuse artifact → M2\nObserved: parse existing structure; no new GPU"),
        ("Missing kinetics", "Expected: evidence → human review\nObserved: registry/evidence route, then block"),
    ]
    y = .86
    for title, body in examples:
        axes[1].text(.04, y, title, fontsize=14, color=PURPLE, fontweight="bold", transform=axes[1].transAxes)
        axes[1].text(.04, y-.10, body, fontsize=11.5, color="#49404e", transform=axes[1].transAxes)
        y -= .22
    fig.suptitle("Galatea Agent Orchestration Benchmark v1", color=PURPLE, fontsize=25, fontweight="bold", y=.98)
    fig.text(.5, .035, "This evaluates orchestration only. M1–M4 scientific results were generated independently by deterministic modules.", ha="center", color="#5d5361", fontsize=11.5)
    fig.subplots_adjust(wspace=.15); fig.tight_layout(rect=(0, .08, 1, .93)); fig.savefig(output / "agent_benchmark_summary.png", dpi=300, facecolor="white"); fig.savefig(output / "agent_benchmark_summary.pdf", facecolor="white"); plt.close(fig)


def matrix(rows: list[dict[str, str]], output: Path) -> None:
    columns = ["routing_correct", "missing_input_handled", "artifact_reuse_correct", "safety_gate_correct", "scientific_boundary_correct", "overall_pass"]
    image = np.array([[int(row[column] == "True") for column in columns] for row in rows])
    fig, ax = plt.subplots(figsize=(10, 7)); ax.imshow(image, cmap=plt.get_cmap("RdPu"), vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(range(len(rows)), [row["case_id"] for row in rows]); ax.set_xticks(range(len(columns)), [name.replace("_", "\n") for name in columns], rotation=0); ax.set_title("Rule-based case capability matrix", color=PURPLE, fontweight="bold", fontsize=19); fig.tight_layout(); fig.savefig(output / "agent_case_matrix.png", dpi=300); plt.close(fig)


def report(output: Path, rule_rows: list[dict[str, str]], llm_rows: list[dict[str, str]], integration_rows: list[dict[str, str]], summary: list[dict[str, object]], head: str) -> None:
    failures = [f"- {row['case_id']}: {row['failure_reason']}" for row in rule_rows if row["overall_pass"] != "True"]
    report_text = f"""# Galatea Agent orchestration benchmark v1

## 1. What was evaluated

The reported M1–M4 scientific results were generated independently by deterministic scientific modules. This benchmark evaluates the Agent as an orchestration layer: task routing, artifact reuse, missing-input handling, human/safety gates, trace production, and scientific-boundary preservation.

Frozen source HEAD before baseline execution: `{head}`. Gold labels in `benchmarks/agent_orchestration_v1/gold_decisions.json` were never passed to the planner.

## 2. What was not evaluated

No M1–M4 scientific sweep, GPU structure prediction, docking, external literature API call, or biological-accuracy claim was evaluated. LLM text was not treated as scientific calculation.

## 3. Benchmark cases

24 frozen cases cover parameter updates, construct changes, reuse, missing input, guardrails, M5 routing, robustness interpretation, safety, API configuration, integrity, and no-recompute behavior.

## 4. Rule-based results

{sum(row['overall_pass'] == 'True' for row in rule_rows)}/24 overall passes. It reliably reuses supplied structure/Vina artifacts and blocks several unsupported shortcuts, but does not implement the requested M3/M5 or construct-change M1→M4 routing.

### Rule-based failures

{chr(10).join(failures) or '- none'}

## 5. LLM results

LLM dry-run was attempted for all 24 identical public tasks using the configured OpenAI-compatible endpoint and model from environment. All 24 calls returned a response, but all plans failed `PlanStep` schema validation (the returned steps used fields such as `id`/`tool` rather than required `step_id`/`objective`, and sometimes `resources: null`). Consequently no accepted LLM AgentTrace exists and its official benchmark score is 0/24. The current client fixes temperature at 0.2; it does not offer a strict deterministic setting.

## 6. End-to-end integration results

Safe `agent run` execution covered cases 11, 12, 14, 21, and 22: {sum(row['overall_pass'] == 'True' for row in integration_rows)}/5 overall passes. No heavy tool was executed; GPU-requested case 21 stopped at the human-approval gate. Raw execution traces are in `results/agent_benchmark_v1/integration/traces/`.

## 7. Failure analysis

- The rule planner has no first-class M1, M3, or M5 workflow routing for the benchmarked project-state changes.
- Artifact integrity flag `artifact_checksum_invalid` is not consumed by the current planner; case 23 attempted reuse rather than rejecting it.
- The LLM prompt asks for `PlanStep-compatible` objects but does not supply a sufficiently strict field-level schema/example, so the backend output is currently unusable without a parser/validation-repair layer.

## 8. Agent limitations

The Agent is currently a conservative partial orchestration prototype. It does not autonomously update approved parameters, infer scientific values, or generate/validate M1–M4 outcomes. Its LLM mode was attempted but did not yield accepted plans in this baseline.

## 9. Recommended next improvements

Implement explicit project-state diff routing (construct vs parameter vs wet-lab update), add M3/M5 plan steps, validate artifact IDs/checksums before reuse, and add a strict LLM JSON schema/example plus repair-free rejection telemetry. Any such change must be benchmarked as v2 on the unchanged v1 cases.

## 10. Exact reproducibility commands

```powershell
python scripts/evaluate_agent_benchmark.py --benchmark benchmarks/agent_orchestration_v1 --output results/agent_benchmark_v1/rule_based --planner rule-based --mode dry-run
python scripts/evaluate_agent_benchmark.py --benchmark benchmarks/agent_orchestration_v1 --output results/agent_benchmark_v1/llm --planner llm --mode dry-run
python scripts/evaluate_agent_benchmark.py --benchmark benchmarks/agent_orchestration_v1 --output results/agent_benchmark_v1/integration --planner rule-based --mode run --integration-only
python scripts/render_agent_benchmark_report.py --results results/agent_benchmark_v1 --benchmark benchmarks/agent_orchestration_v1
```
"""
    (output / "AGENT_BENCHMARK_REPORT.md").write_text(report_text, encoding="utf-8")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--results", type=Path, default=Path("results/agent_benchmark_v1")); parser.add_argument("--benchmark", type=Path, default=Path("benchmarks/agent_orchestration_v1")); args = parser.parse_args()
    rule_rows = read_csv(args.results / "rule_based" / "agent_benchmark_results.csv"); llm_rows = read_csv(args.results / "llm" / "agent_benchmark_results.csv"); integration_rows = read_csv(args.results / "integration" / "agent_benchmark_results.csv")
    rule, llm = aggregate(rule_rows), aggregate(llm_rows)
    summary = [{"metric": key, "Rule-based": f"{rule[key]:.3f}", "LLM Agent": f"{llm[key]:.3f}"} for key in rule]
    write_csv(args.results / "agent_planner_summary.csv", summary); figure(rule, llm, args.results); matrix(rule_rows, args.results)
    head = subprocess.check_output(["git", "rev-parse", "adcadf7"], text=True).strip()
    report(args.results, rule_rows, llm_rows, integration_rows, summary, head)
    print(f"rendered {args.results}")


if __name__ == "__main__": main()
