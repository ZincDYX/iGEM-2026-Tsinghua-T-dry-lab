# ADR: local modular runtime with one external-tool boundary

Status: accepted for the M1–M4 implementation.

## Context

The workflow combines exact scientific equations, asynchronous predictors, local GPU tools, licensed services, and wet-lab evidence. Splitting each predictor into a service or adapter subclass would add deployment and pass-through code without changing the scientific contract. Conversely, putting sequence QC, structural scoring, phase equilibrium, and reaction kinetics into one function would hide independent assumptions and make formula review difficult.

The design review used two supplied books as principles rather than instructions: *A Philosophy of Software Design* (deep modules, information hiding, different layers should provide different abstractions) and *Software Architecture: The Hard Parts* (trade-off analysis, explicit contracts, and fitness functions). No book example was copied into the scientific implementation.

## Decision

- Keep a local modular monolith. Scientific modules own typed inputs, equations, validation, and result models; MCP and CLI are transports over the same functions.
- Use one `ExternalToolAdapter` execution boundary. Tool-specific scientific parsing remains in focused parser modules; empty tool-specific subclasses are removed.
- Keep strict checks only where they protect a scientific invariant, provenance, external process boundary, unit, or irreversible output. Missing optional predictors produce an explicit blocked/insufficient result instead of fabricated values.
- Make cross-module numerical functions public only when another module legitimately depends on them. The two-phase competitive rate function is therefore `phase_competitive_rates`, not a private helper imported elsewhere.
- Keep the Markdown steady-state reaction identity loader separate from the legacy author-native kinetics loader. The former reads exactly four identity columns; it must not demand unused author-native kinetic columns.
- Treat deployment size and tool availability as executable contracts through `igem.compute.audit_deployment` and external-tool run manifests.

## Rejected alternatives

- A microservice per scientific tool: too much operational coupling for one local workflow, with no independent scaling or ownership need.
- One adapter subclass per command: shallow modules that merely inherit behavior and obscure the common execution policy.
- Automatic fallbacks and guessed defaults: they can turn missing measurements, credentials, or artifacts into apparently valid scientific results.
- Bundling every optional simulation stack: unnecessary for the formal M1–M4 path. The local deployment limit is 15 GB (15,000,000,000 bytes); separately managed compute-server installations are exempt. The earlier 10 GiB interpretation of the original 10 GB requirement was incorrect; see the corrected deployment audit.

## Consequences

The code can run locally or through the MCP server without duplicating formulas. Licensed predictors and public APIs remain explicit deployment boundaries. Adding a tool requires a catalog record, command configuration, raw artifact, parser where needed, and a smoke test; it does not require a new service or empty class.

## Production Assistant and responsibility boundaries

The workbench uses one execution path:

```text
Assistant request -> PlanningService -> semantic interpretation (optional model)
                                    -> deterministic compiler / registered workflow
                                    -> saved proposal for human review
Accepted proposal + separate Run -> WorkflowEngine -> registered tools / MCP
                                                   -> durable results and events
```

`PlanningService` observes the actual saved project, compiles the request,
expands required predecessors, binds the review identity and persists the
proposal and conversation. These are separate private operations, not new
services or alternative executors. Proposal creation never launches a job.
The caller's execution policy is retained; missing evidence, stale review
identities and unverified cross-run reuse do not become permissions.

The optional model returns a typed semantic decision, not shell commands,
scientific parameters or an arbitrary executable DAG. The deterministic
compiler selects registered stages. `agent/runtime.py` remains a deprecated
compatibility API used by historical CLI experiments and tests, so it cannot
be deleted merely because the workbench does not use it. It is not a second
production executor.

Assistant settings own private credentials and bounded connection probes.
Model discovery, JSON output, native function calling and streaming are tested
independently: one observed capability never implies that the others work.
Native function calling is not required by the semantic-JSON compiler route;
a failed function-calling probe is not described as successful tool use.
No model address, deployment identifier or credential belongs in project files,
source bundles or repository defaults.

The frontend shares one typed save/request/publish guard for proposal entry
points. Input or proposal invalidation during an asynchronous operation still
discards its obsolete response. Presentation of changed bindings is separate
from conversation loading and proposal actions. Unused goal/mode callbacks
are not passed into components that cannot edit those settings.

### Verification and limits (2026-10-17)

- Seven identical before/after semantic cases matched, including missing
  measurements, expanded dependencies, unavailable stages, missing disclosure
  consent and a forbidden tool request. These were software fixtures, not
  biological evidence or genuine tool predictions.
- Four additional backend cases fix the expected dependency, permission,
  missing-input and transcript behavior; frontend tests cover obsolete async
  responses, grouped changes and real formula-variable presentation.
- A private real-provider check observed JSON and streaming, but did not
  verify native function calling. Three planning requests and a built-browser
  request returned saved, blocked proposals; no scientific job was started.
  Missing-concentration explanations were useful, but the new-design request
  also refused to plan because later-stage evidence was absent. Reliable
  successful autonomous planning is therefore not established by this check.
- The built browser displayed the real response and reopened its persisted
  conversation without page errors. This validates selected integration
  behavior, not scientific correctness or a non-expert usability study.
- Server regression: 1,093 passed and 28 explicitly skipped in the general
  test environment with author references required. Providing the existing
  external inputs separately passed all 37 tests in the Mpipi/2PDZ/PS-v3
  group; the existing QM environment passed 22 tests and skipped the GPU
  case because no CUDA device was assigned to that test. Skips are not
  evidence of successful native execution. The frontend passed 90 tests
  in 29 files, TypeScript checks and a production build.

The review combined a whole tracked-source structure scan with targeted manual
inspection; it was not a line-by-line certification of every file. Large
scientific stage functions, API route grouping and the workspace coordinator
remain maintenance hotspots. Generated contracts, retained compatibility APIs
and independently versioned scientific equations are not dead code merely
because their files are large. Further extractions must retain their own
characterization tests; no new framework, formula change or GPU-budget change
is justified by this refactor.
