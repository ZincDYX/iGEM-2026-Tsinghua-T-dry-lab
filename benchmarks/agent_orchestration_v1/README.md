# Agent orchestration benchmark v1

This frozen benchmark evaluates planning and safe execution routing for the Galatea dry-lab Agent. It does **not** evaluate biological accuracy and does not claim that the Agent generated M1--M4 scientific results.

`benchmark_cases.jsonl` is passed to the planner only after each row is reduced to the public `AgentTask` fields: `task_id`, `objective`, `inputs`, `constraints`, `artifacts_dir`, `require_human_approval`, and `max_replans`. `gold_decisions.json` is consumed only by the deterministic evaluator after traces are saved.

The cases and gold labels were committed before the baseline runs. Results are ignored local artifacts under `results/agent_benchmark_v1/`.
