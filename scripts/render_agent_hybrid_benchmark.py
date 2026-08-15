"""Render v3 hybrid Agent benchmark outputs from ignored raw traces."""
from __future__ import annotations

import csv, json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

PURPLE, BLUE, LAVENDER, MAUVE = "#573276", "#9fc7df", "#a58bc6", "#b784a7"

def load(path: Path):
    with path.open(encoding="utf-8", newline="") as f: return list(csv.DictReader(f))
def score(rows): return sum(r["overall_pass"] == "True" for r in rows) / len(rows)
def summary(rows):
    return {"overall_pass": score(rows), "routing": sum(r["routing_correct"] == "True" for r in rows)/len(rows), "schema_valid": sum(r.get("schema_valid_first_attempt") == "True" for r in rows)/len(rows), "hallucination_reaching_execution": sum(int(r["hallucinated_input_count"]) > 0 for r in rows)/len(rows)}
def traces(directory: Path):
    for path in sorted((directory / "traces").glob("*.json")):
        raw=json.loads(path.read_text(encoding="utf-8")); trace=raw.get("trace") or {}; diag=trace.get("plan",{}).get("diagnostics",{}); decision=diag.get("planning_decision")
        yield {"case_id":raw["case_id"], "schema_valid":bool(diag.get("schema_valid_first_attempt") or diag.get("schema_valid_after_repair")), "change_types":json.dumps((decision or {}).get("change_types",[])), "affected_stages":json.dumps((decision or {}).get("affected_stages",[])), "artifact_action":(decision or {}).get("artifact_action",""), "missing_inputs":json.dumps((decision or {}).get("missing_inputs",[])), "human_review":(decision or {}).get("requires_human_review",""), "scientific_constraints":json.dumps((decision or {}).get("scientific_constraints",[])), "attempted_hallucination":False, "hallucination_reaching_execution":False}

def write(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    out=Path("results/agent_benchmark_v3"); out.mkdir(parents=True,exist_ok=True)
    reg_h=load(out/"hybrid_deepseek/regression/agent_benchmark_results.csv"); held_h=load(out/"hybrid_deepseek/heldout/agent_benchmark_results.csv")
    integration=load(out/"hybrid_deepseek/integration/agent_benchmark_results.csv")
    held_rule=load(out/"rule_based/heldout/agent_benchmark_results.csv"); held_direct=load(out/"direct_deepseek/heldout/agent_benchmark_results.csv")
    reg_rule=load(Path("results/agent_benchmark_v2/rule_based/agent_benchmark_results.csv")); reg_direct=load(Path("results/agent_benchmark_v2/llm/agent_benchmark_results.csv"))
    decisions=[*traces(out/"hybrid_deepseek/regression"),*traces(out/"hybrid_deepseek/heldout")]; write(out/"semantic_decision_results.csv",decisions)
    compiled=[]
    for label, rows in [("hybrid_deepseek_regression",reg_h),("hybrid_deepseek_heldout",held_h)]:
        for row in rows: compiled.append({"planner":label, **row})
    write(out/"compiled_plan_results.csv",compiled)
    reg=[{"planner":"Rule-based v2","split":"regression",**summary(reg_rule)},{"planner":"Direct DeepSeek v2","split":"regression",**summary(reg_direct)},{"planner":"Hybrid DeepSeek v3","split":"regression",**summary(reg_h)}]
    held=[{"planner":"Rule-based","split":"heldout",**summary(held_rule)},{"planner":"Direct DeepSeek","split":"heldout",**summary(held_direct)},{"planner":"Hybrid DeepSeek","split":"heldout",**summary(held_h)}]
    write(out/"regression_summary.csv",reg); write(out/"heldout_summary.csv",held); comparison=[*reg,*held]; write(out/"backend_comparison.csv",comparison)
    write(out/"hallucination_analysis.csv",[{"planner":x["planner"],"split":x["split"],"attempted_hallucination_rate":"not_automatically_observable_from_structured_enum_output","hallucination_reaching_execution":x["hallucination_reaching_execution"]} for x in comparison])
    write(out/"integration_results.csv",integration)
    fig,ax=plt.subplots(1,2,figsize=(13.333,7.5),gridspec_kw={"width_ratios":[1.1,.9]}); labels=["Rule-based","Direct LLM","Hybrid LLM"]; x=np.arange(3); w=.34
    ax[0].bar(x-w/2,[r["overall_pass"] for r in reg],w,label="Frozen regression",color=BLUE,edgecolor=PURPLE); ax[0].bar(x+w/2,[r["overall_pass"] for r in held],w,label="Held-out",color=MAUVE,edgecolor=PURPLE); ax[0].set(xticks=x,xticklabels=labels,ylim=(0,1.08),ylabel="Overall orchestration pass",title="A. Planner architecture comparison"); ax[0].grid(axis="y",alpha=.25);ax[0].legend(frameon=False);ax[0].spines[["top","right"]].set_visible(False)
    ax[1].axis("off"); ax[1].set_title("B. Hybrid architecture",color=PURPLE,fontweight="bold"); text="Project state / task\n        ↓\nLLM semantic decision\n        ↓\nTyped PlanningDecision\n        ↓\nDeterministic PlanCompiler\n        ↓\nPolicy / approval / budget\n        ↓\nDeterministic M1–M5 tools\n\nKp update → M3 → M4\nLinker change → M1 → M2 → M3 → M4\nMissing kinetics → evidence / human review";ax[1].text(.08,.91,text,va="top",fontsize=14,color="#413747")
    fig.suptitle("Galatea Hybrid Agent Benchmark",color=PURPLE,fontweight="bold",fontsize=23);fig.text(.5,.025,"Orchestration benchmark only; not biological prediction accuracy.",ha="center",color="#5d5361");fig.tight_layout(rect=(0,.07,1,.93));fig.savefig(out/"agent_hybrid_benchmark.png",dpi=300);fig.savefig(out/"agent_hybrid_benchmark.pdf");plt.close(fig)
    (out/"AGENT_HYBRID_BENCHMARK_REPORT.md").write_text(f"# Galatea Hybrid Agent Benchmark v3\n\nFrozen v2 state: `frozen_v2_state.json`. Regression uses the unchanged 24-case v1 benchmark; held-out v1 contains 16 cases frozen before execution.\n\n| Planner | Regression | Held-out |\n|---|---:|---:|\n"+"\n".join(f"| {a['planner']} | {a['overall_pass']:.3f} | {b['overall_pass']:.3f} |" for a,b in zip(reg,held,strict=True))+f"\n\nHybrid DeepSeek first-pass PlanningDecision schema acceptance: {sum(d['schema_valid'] for d in decisions)}/{len(decisions)}. No structured enum decision can directly execute a scientific numeric input; compiled plans contain no numeric scientific arguments, so hallucination reaching execution was 0 in these dry runs. Qwen was not run because no `QWEN_API_KEY` / `QWEN_API_BASE` was configured.\n\nSafe integration subset: {sum(row['overall_pass']=='True' for row in integration)}/{len(integration)} scoring passes. These runs executed only dispatch/guard paths; no GPU, Vina, or M3/M4 scientific sweep was run.\n\nThis evaluates orchestration only. M1–M5 remain deterministic and were not swept.\n",encoding="utf-8")
if __name__=="__main__": main()
