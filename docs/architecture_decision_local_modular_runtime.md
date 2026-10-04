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
- Bundling every optional simulation stack: unnecessary for the formal M1–M4 path. The user updated the deployment limit to 15 GB (15,000,000,000 bytes) on 2026-10-04. The earlier 10 GiB interpretation of the original 10 GB requirement was incorrect; see the corrected deployment audit.

## Consequences

The code can run locally or through the MCP server without duplicating formulas. Licensed predictors and public APIs remain explicit deployment boundaries. Adding a tool requires a catalog record, command configuration, raw artifact, parser where needed, and a smoke test; it does not require a new service or empty class.
