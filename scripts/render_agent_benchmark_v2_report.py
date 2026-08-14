"""Render an honest v1→v2 orchestration comparison from frozen benchmark traces."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PURPLE, BLUE, LAVENDER, MAUVE, GRID = "#573276", "#9fc7df", "#a58bc6", "#b784a7", "#e7dfea"
METRICS = [("Routing", "routing_correct"), ("Missing input", "missing_input_handled"), ("Artifact reuse", "artifact_reuse_correct"), ("Safety", "safety_gate_correct"), ("Scientific boundary", "scientific_boundary_correct"), ("Overall pass", "overall_pass")]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle: return list(csv.DictReader(handle))


def fraction(data: list[dict[str, str]], field: str) -> float:
    return sum(row.get(field) == "True" for row in data) / len(data)


def main() -> None:
    root = Path("results/agent_benchmark_v2"); root.mkdir(parents=True, exist_ok=True)
    v1_rule = rows(Path("results/agent_benchmark_v1/rule_based/agent_benchmark_results.csv"))
    v1_llm = rows(Path("results/agent_benchmark_v1/llm/agent_benchmark_results.csv"))
    v2_rule = rows(root / "rule_based/agent_benchmark_results.csv")
    v2_llm = rows(root / "llm/agent_benchmark_results.csv")
    comparison = []
    for label, field in METRICS:
        comparison.append({"metric": label, "rule_based_v1": f"{fraction(v1_rule, field):.3f}", "rule_based_v2": f"{fraction(v2_rule, field):.3f}", "llm_v1": f"{fraction(v1_llm, field):.3f}", "llm_v2": f"{fraction(v2_llm, field):.3f}"})
    with (root / "benchmark_v1_vs_v2.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparison[0])); writer.writeheader(); writer.writerows(comparison)
    with (root / "agent_benchmark_v2_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(v2_rule[0])); writer.writeheader(); writer.writerows(v2_rule)
    schema = [{"case_id": row["case_id"], "first_pass_valid": row.get("schema_valid_first_attempt", "False"), "valid_after_repair": row.get("schema_valid_after_repair", "False"), "rejected": str(row.get("schema_valid_first_attempt") != "True" and row.get("schema_valid_after_repair") != "True")} for row in v2_llm]
    with (root / "llm_schema_validation.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(schema[0])); writer.writeheader(); writer.writerows(schema)

    fig, axes = plt.subplots(1, 2, figsize=(13.333, 7.5), gridspec_kw={"width_ratios": [1.35, .8]})
    labels = [item[0].replace(" ", "\n") for item in METRICS]; fields = [item[1] for item in METRICS]; x = np.arange(len(labels)); width = .24
    for offset, data, label, color in [(-width, v1_rule, "Rule v1", LAVENDER), (0, v2_rule, "Rule v2", BLUE), (width, v2_llm, "LLM v2", MAUVE)]:
        axes[0].bar(x + offset, [fraction(data, item) for item in fields], width, label=label, color=color, edgecolor=PURPLE)
    axes[0].set(xticks=x, xticklabels=labels, ylim=(0, 1.08), ylabel="Fraction of applicable frozen cases", title="A. Orchestration performance")
    axes[0].grid(axis="y", color=GRID); axes[0].set_axisbelow(True); axes[0].spines[["top", "right"]].set_visible(False); axes[0].legend(frameon=False)
    axes[0].text(.01, .02, "LLM v1: 0/24 accepted because of schema integration failure.", transform=axes[0].transAxes, fontsize=9, color="#5d5361")
    axes[1].axis("off"); axes[1].set_title("B. Observed v2 routing", color=PURPLE, fontweight="bold")
    examples = [("New Kp9", "M3 → M4"), ("Linker changed", "M1 → M2 → M3 → M4"), ("Existing structure", "reuse artifact → M2"), ("Missing kinetics", "evidence → human review / block")]
    y = .86
    for title, path in examples:
        axes[1].text(.04, y, title, transform=axes[1].transAxes, color=PURPLE, fontweight="bold", fontsize=14); axes[1].text(.04, y-.09, path, transform=axes[1].transAxes, fontsize=12, color="#49404e"); y -= .21
    fig.suptitle("Galatea Agent Orchestration Benchmark v1 vs v2", color=PURPLE, fontsize=23, fontweight="bold")
    fig.text(.5, .03, "Frozen project-specific regression benchmark; orchestration accuracy is not biological prediction accuracy.", ha="center", color="#5d5361")
    fig.tight_layout(rect=(0, .07, 1, .93)); fig.savefig(root / "agent_benchmark_v1_vs_v2.png", dpi=300); fig.savefig(root / "agent_benchmark_v1_vs_v2.pdf"); plt.close(fig)
    first = sum(row["first_pass_valid"] == "True" for row in schema); repaired = sum(row["valid_after_repair"] == "True" for row in schema); rejected = len(schema) - first - repaired
    (root / "AGENT_BENCHMARK_V2_REPORT.md").write_text(f"""# Galatea Agent Orchestration Benchmark v2

The v1 benchmark inputs and gold labels were reused unchanged from `benchmarks/agent_orchestration_v1/`. v2 changes only orchestration interfaces: typed project-state routing, artifact integrity guard, stage-dispatch wrapper, and JSON Output schema validation with at most one repair attempt.

| Metric | Rule v1 | Rule v2 | LLM v1 | LLM v2 |
|---|---:|---:|---:|---:|
""" + "\n".join(f"| {row['metric']} | {row['rule_based_v1']} | {row['rule_based_v2']} | {row['llm_v1']} | {row['llm_v2']} |" for row in comparison) + f"""

## LLM schema telemetry

- First-pass valid: {first}/{len(schema)}
- Accepted after one repair: {repaired}/{len(schema)}
- Rejected: {rejected}/{len(schema)}

This benchmark measures frozen project-specific orchestration only. It does not demonstrate general scientific intelligence or biological prediction accuracy. No M1–M4 scientific sweep was run.
""", encoding="utf-8")


if __name__ == "__main__": main()
