# Architecture: one production workflow engine, explicit tool boundaries

Status: accepted. This describes the implementation, not a claim of autonomous
scientific validation. The design uses information hiding, deep modules and
explicit trade-offs from the two supplied architecture books; no examples were copied.

## Execution path

```text
Desktop / browser / CLI -> ApplicationService
Assistant request -> PlanningService -> optional semantic model
                                    -> deterministic workflow compiler
                                    -> persisted proposal -> human review
Accepted proposal + separate Run -> WorkflowEngine -> registered builtin handler
                                                  -> scientific stdio MCP
                                                  -> trusted plugin subprocess
                                 -> SQLite events, attempts and artifacts
```

The model proposes typed intent, not executable shell commands or scientific
numbers. A proposal does not start a job or approve parameters. Workflow review,
parameter approval and execution are separate operations.

| Boundary | Implemented behavior | Limit |
| --- | --- | --- |
| Runtime | One bounded tool pool and controller queue; SQLite snapshots, leases, heartbeats, map shards, joins and selective retry | Process-local GPU slot, not a cluster scheduler; memory limits are rejected rather than pretended |
| MCP | Real stdio discovery and calls, validated schemas and structured errors; filtered child environment | Each call starts a child process; MCP is a protocol, not a security sandbox |
| Plugins | Explicit trust, independent venv, subprocess JSON IO, pinned dependency lock, source-bound capability grants and selected secrets | **No OS sandbox**: trusted code still has the current user's filesystem/network privileges |
| Model connection | Private settings; JSON, native tool calls and streaming probed independently | One observed capability does not establish the others or scientific validity |

Pausing/cancelling stops further dispatch and controls publication. It does not
guarantee immediate termination of an already running native or remote job.
Timeout tree cleanup at the external-command boundary is a different operation.
Unknown external submissions require reconciliation, not blind resubmission.

## Responsibility and compatibility

- Scientific modules own equations, units, input models and interpretations.
  MCP/CLI wrappers call those functions; they do not reimplement the science.
- `PlanningService` owns observations, compiled requests, required predecessors,
  review binding and transactional proposal/conversation records.
  `Workflow.required_nodes` is shared by planning and execution; it does not
  change stage order or imply verified cross-run artifact reuse.
- `WorkflowEngine` owns immutable execution, attempt identity and publication.
  Its source-digest cache lives only within one snapshot/review/verification:
  identical sources give identical hashes, and a new review rereads files.
- `ExternalToolAdapter` owns configured command execution and raw manifests;
  focused parsers interpret native output. No empty adapter subclasses or
  service-per-predictor layer is needed.
- The frontend shares typed proposal guards and workflow-document updates.
  Obsolete async responses are discarded. View-only edits do not resend the
  scientific DAG or grant execution authority.
- `agent/runtime.py` is a **retained legacy runtime**, used by historical CLI
  experiments and callers with JSONL memory/traces. It is not the workbench's
  executor, and the two runtime APIs have **not** been fully migrated into one.
  Deleting it would remove existing behavior, not just dead code.

Keep distinct scientific contracts distinct: the four-column Markdown reaction
identity loader and author-native kinetics loader have different input semantics.
Likewise, OS isolation, dependency isolation, execution permission, provenance
verification and authentication are not interchangeable checks.

Missing tools, measurements or evidence stay explicit. No automatic numerical
fallback or guessed parameter is an acceptable simplification. Model endpoints,
deployment identifiers and credentials stay out of repositories, projects and
source bundles. The local tool limit is 15 GB; separately managed compute-server
installations are exempt. Tool/data/model licenses remain independent.

## Verification and remaining limits — 2026-10-17

The infrastructure refactor retained all 56 stdio tool schemas/signatures;
112 forwarding cases, five semantic planning cases and eight persisted revision
diffs matched the previous implementation. Server tests: **1,119 passed,
9 skipped**, including supplied native Mpipi/2PDZ/PS-v3 references. Independent
QM tests: **22 passed, 1 GPU skip**. Skips are not successful native executions.
Frontend: **91 passed**, plus type checking and a production build.

A private real-provider check observed JSON and streaming, not native function
calling. Three planning requests and one built-browser request returned saved
blocked proposals without starting science. Missing-concentration explanations
were useful; successful autonomous planning on a complete project remains
unverified. The browser displayed and reopened the actual replies without page
errors. This was software-fixture acceptance, not biological or novice-usability validation.

The review was a tracked-source structure scan plus targeted manual inspection,
not a line-by-line correctness certification. Large scientific stage functions,
API route grouping and workspace coordination remain maintenance hotspots.
Generated contracts and compatibility APIs are not dead merely because they are
large. Further migration must preserve their contracts and tests; microbenchmarks
and reduced source size do not establish whole-app performance or award eligibility.
