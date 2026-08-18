# Evidence GraphRAG and Agent baseline matrix

## Scope and scientific boundary

The knowledge graph is a retrieval index over existing evidence records. It
does not infer missing biological facts and does not approve a
`ParameterRecord`. Nodes and edges are generated deterministically from the
stored record fields, DOI, title, and evidence quote.

```text
Paper -> CONTAINS -> Experiment -> SUPPORTED_BY -> EvidenceSpan
                              -> USES_ENZYME -> Enzyme
                              -> USES_SUBSTRATE -> Substrate
                              -> PRODUCES -> Product
                              -> PERFORMED_IN -> Host
                              -> REPORTS_METRIC -> Metric
                              -> USES_LLPS_COMPONENT/TRIGGER -> LLPS entity
                              -> AT_TEMPERATURE/AT_PH/FOR_DURATION -> Condition
```

Unknown, empty, and `not reported` values are not turned into graph entities.
Every relation retains `record_id`, DOI, and the evidence quote. A saved graph
also stores an evidence fingerprint; QA ignores a stale graph and rebuilds it
in memory.

## Build and query

```powershell
igem-drylab literature build-graph `
  --evidence essay/project_conditioned_evidence_database.csv `
  --output outputs/evidence_graph.json

igem-drylab literature qa "DMT activity in yeast LLPS condensates" `
  --evidence essay/project_conditioned_evidence_database.csv `
  --graph --graph-path outputs/evidence_graph.json
```

Semantic retrieval can be enabled independently:

```powershell
igem-drylab literature qa "DMT activity in yeast LLPS condensates" `
  --evidence essay/project_conditioned_evidence_database.csv `
  --semantic --graph --graph-path outputs/evidence_graph.json
```

The three routes are fused by reciprocal rank fusion (RRF). DOI/text
deduplication and MMR are applied afterwards. Each source includes
`graph_rank`, matched entities, and graph paths so its selection is auditable.

The local browser can use the same route:

```powershell
igem-drylab literature serve-qa `
  --evidence essay/project_conditioned_evidence_database.csv `
  --graph --graph-path outputs/evidence_graph.json
```

For the local tool registry, pass `graph_enabled: true` and optional
`graph_path` to `igem.literature.qa`.

## Agent baseline matrix

The comparison separates provider from architecture:

| Profile | Planner architecture | Provider |
|---|---|---|
| `rule_based` | deterministic rules | local |
| `qwen` | direct LLM DAG planning | Qwen |
| `deepseek` | direct LLM DAG planning | DeepSeek |
| `hybrid_qwen` | LLM semantic decision + deterministic compiler | Qwen |
| `hybrid_deepseek` | LLM semantic decision + deterministic compiler | DeepSeek |

Configure credentials only in `.env`. Qwen requires an explicit endpoint so a
Qwen key can never be accidentally sent to a DeepSeek endpoint.

```dotenv
QWEN_API_KEY=
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
QWEN_MODEL=qwen3-235b-a22b-instruct-2507

DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=https://api.deepseek.com/chat/completions
DEEPSEEK_MODEL=deepseek-chat
```

Run every configured profile on the same frozen held-out cases:

```powershell
python scripts/run_agent_baseline_matrix.py `
  --benchmark benchmarks/agent_orchestration_heldout_v2 `
  --output-root results/agent_baseline_matrix `
  --jobs 5
```

Unconfigured providers are reported as skipped. Add `--strict` to fail instead.
The matrix writes per-case traces, a combined case table, summary CSV/JSON, and
`AGENT_BASELINE_MATRIX_REPORT.md`.

Reported dimensions include routing, missing-input handling, artifact reuse,
safety gates, scientific-boundary preservation, overall pass rate, forbidden
actions, hallucinated scientific inputs, schema validity, latency, and token
usage. The benchmark measures orchestration, not biological accuracy.

## Fair-comparison requirements

- Use the same frozen benchmark and gold labels for all profiles.
- Use identical public `AgentTask` fields and the same deterministic scorer.
- Keep mode, concurrency, retries, and case selection identical.
- Do not expose gold decisions to any planner.
- Report model names, skipped/failed calls, token usage, and latency.
- Compare direct and hybrid architectures separately; provider quality and
  architecture safety are different experimental factors.
